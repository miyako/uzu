"""Exercise the dependency-free Pages build and all generated local links."""

import importlib.util
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("site_build", ROOT / "site" / "build.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
OUTPUT = ROOT / "site" / "_site"


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.tags = []
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        self.elements.append((tag, attrs))
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError(f"duplicate id: {attrs['id']}")
            self.ids.add(attrs["id"])
        for attribute in ("href", "src"):
            if attribute in attrs:
                self.links.append(attrs[attribute])


class SiteTests(unittest.TestCase):
    def check_build(self, base):
        BUILDER.build(OUTPUT, base)
        self.assertEqual(
            {path.name for path in OUTPUT.iterdir()},
            {"index.html", "guide.html", "style.css", "logo.png", ".nojekyll"},
        )
        pages = {}
        for path in OUTPUT.glob("*.html"):
            source = path.read_text(encoding="utf-8")
            self.assertTrue(source.startswith("<!doctype html>"))
            self.assertNotIn("{{", source)
            self.assertIn('lang="en"', source)
            self.assertIn('name="viewport"', source)
            page = pages[path.name] = Page(source)
            for tag in ("title", "nav", "main", "footer"):
                self.assertIn(tag, page.tags)
            self.assertEqual(page.tags.count("h1"), 1)
            self.assertTrue(any(
                tag == "main" and attrs.get("id") == "main"
                and attrs.get("tabindex") == "-1"
                for tag, attrs in page.elements
            ))
            self.assertTrue(any(
                tag == "nav" and attrs.get("aria-label")
                for tag, attrs in page.elements
            ))
            self.assertEqual(sum(
                attrs.get("aria-current") == "page"
                for _, attrs in page.elements
            ), 1)
            self.assertTrue(any(
                tag == "a" and attrs.get("class") == "skip"
                and attrs.get("href") == "#main"
                for tag, attrs in page.elements
            ))
            for tag, attrs in page.elements:
                if tag == "th":
                    self.assertIn(attrs.get("scope"), ("row", "col"))
            if path.name == "index.html":
                self.assertTrue(any(
                    attrs.get("class") == "engine-panel"
                    and attrs.get("role") == "group"
                    and attrs.get("aria-label")
                    for _, attrs in page.elements
                ))
                self.assertIn('<div class="connection">loads</div>', source)
                self.assertIn("HTTP / 127.0.0.1:8080", source)
                self.assertIn("Catalog ID, Hugging Face repo or local directory", source)
                self.assertIn('class="file-mark" aria-hidden="true">MODEL', source)

        for name, page in pages.items():
            for link in page.links:
                with self.subTest(page=name, link=link, base=base):
                    target = urlsplit(link)
                    if target.scheme or target.netloc:
                        self.assertEqual(target.scheme, "https")
                        continue
                    if target.path:
                        self.assertTrue(target.path.startswith(base), link)
                        relative = unquote(target.path[len(base):]) or "index.html"
                    else:
                        relative = name
                    destination = OUTPUT / relative
                    self.assertTrue(destination.resolve().is_relative_to(OUTPUT.resolve()))
                    self.assertTrue(destination.is_file(), link)
                    if target.fragment:
                        self.assertIn(unquote(target.fragment), pages[relative].ids)

    def test_project_base_and_output(self):
        self.check_build("/uzu/")

    def test_configurable_base(self):
        try:
            self.check_build("/preview/uzu/")
        finally:
            BUILDER.build(OUTPUT, "/uzu/")

    def test_reject_invalid_base(self):
        for base in ("uzu/", "/uzu", "//example.com/", "/../", "/uzu/?x=1"):
            with self.subTest(base=base), self.assertRaises(ValueError):
                BUILDER.build(OUTPUT, base)


if __name__ == "__main__":
    unittest.main()
