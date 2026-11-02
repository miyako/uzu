#!/usr/bin/env python3
"""Build the standalone documentation site with only the Python standard library."""

import argparse
import re
import shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ICON = SOURCE.parent / "uzu" / "Resources" / "logo.png"
REPO = "https://github.com/miyako/uzu"


def build(output: Path, base_path: str = "/uzu/") -> None:
    if not re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)*", base_path):
        raise ValueError("base path must be an absolute directory path, such as /uzu/")
    output.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "guide.html"):
        page = (SOURCE / name).read_text(encoding="utf-8")
        page = page.replace("{{BASE}}", base_path).replace("{{REPO}}", REPO)
        if "{{" in page:
            raise ValueError(f"unresolved template value in {name}")
        (output / name).write_text(page, encoding="utf-8")
    shutil.copyfile(SOURCE / "style.css", output / "style.css")
    shutil.copyfile(ICON, output / "logo.png")
    (output / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-path", default="/uzu/")
    parser.add_argument("--output", type=Path, default=SOURCE / "_site")
    args = parser.parse_args()
    build(args.output, args.base_path)
