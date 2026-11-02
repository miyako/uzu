import hashlib
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load_script("install-native")
packager = load_script("package-info")


class NativeReleaseTests(unittest.TestCase):
    def release(self, tag="server-0.6.15-abcd-1-1", **changes):
        release = {
            "tag_name": tag,
            "draft": False,
            "prerelease": False,
            "assets": [{"name": name} for name in installer.REQUIRED_ASSETS],
        }
        release.update(changes)
        return release

    def test_selects_complete_native_not_component_latest(self):
        pages = [[self.release("20.0.3"), self.release(draft=True)],
                 [self.release(assets=[]), self.release(prerelease=True), self.release()]]
        self.assertEqual(installer.select_release(pages), "server-0.6.15-abcd-1-1")

    def test_no_native_is_explicit_error(self):
        with self.assertRaisesRegex(RuntimeError, "run Update server first"):
            installer.select_release([[self.release("20.0.3")]])

    def test_checksum_missing_ambiguous_or_corrupt_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "archive.tar.gz").write_bytes(b"fixture")
            digest = hashlib.sha256(b"fixture").hexdigest()
            line = f"{digest}  archive.tar.gz\n"
            (directory / "SHA256SUMS").write_text(line)
            installer.verify_checksum(directory, "archive.tar.gz")
            for content in ("", line + line, "0" * 64 + "  archive.tar.gz\n"):
                with self.subTest(content=content):
                    (directory / "SHA256SUMS").write_text(content)
                    with self.assertRaises(RuntimeError):
                        installer.verify_checksum(directory, "archive.tar.gz")

    def test_tar_data_filter_rejects_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with tarfile.open(directory / "bad.tar", "w") as archive:
                member = tarfile.TarInfo("../outside")
                member.size = 1
                archive.addfile(member, io.BytesIO(b"x"))
            with tarfile.open(directory / "bad.tar") as archive:
                with self.assertRaises(tarfile.OutsideDestinationError):
                    archive.extractall(directory / "output", filter="data")
            self.assertFalse((directory / "outside").exists())

    def test_exact_release_install_verifies_payload_and_copies_notices(self):
        info = {"target": "aarch64-apple-darwin", "source_sha": "a" * 40}
        with tempfile.TemporaryDirectory() as temporary, contextlib.chdir(temporary):
            root = Path(temporary)
            payload = root / "fixture/uzu-server-macos-arm64"
            payload.mkdir(parents=True)
            (payload / "cli").write_bytes(b"unit-test executable fixture")
            (payload / "cli").chmod(0o755)
            (payload / "BUILD-INFO.json").write_text(json.dumps(info))
            (payload / "LICENSE-UZU").write_text("upstream license")

            def run(args, check):
                self.assertTrue(check)
                if args[0] == "gh":
                    self.assertEqual(args[3], "server-exact-1")
                    download = Path(args[args.index("--dir") + 1])
                    with tarfile.open(download / installer.ARCHIVE, "w:gz") as archive:
                        archive.add(payload, arcname=payload.name)
                    (download / "BUILD-INFO.json").write_text(json.dumps(info))
                    sums = []
                    for filename in (installer.ARCHIVE, "BUILD-INFO.json"):
                        digest = hashlib.sha256((download / filename).read_bytes()).hexdigest()
                        sums.append(f"{digest}  {filename}")
                    (download / "SHA256SUMS").write_text("\n".join(sums) + "\n")
                else:
                    self.assertEqual(args[:2], ["bash", "scripts/smoke-native.sh"])
                    self.assertTrue(os.access(args[2], os.X_OK))

            with patch.dict(os.environ, {"GH_REPO": "miyako/uzu", "SERVER_TAG": "server-exact-1",
                                         "GITHUB_STEP_SUMMARY": ""}):
                with patch.object(installer.subprocess, "run", side_effect=run):
                    installer.install()
            installed = root / "uzu/Resources/bin/macOS"
            self.assertEqual((installed / "LICENSE-UZU").read_text(), "upstream license")
            self.assertEqual(json.loads((installed / "BUILD-INFO.json").read_text()), info)
            self.assertTrue(os.access(installed / "cli", os.X_OK))

    def test_package_provenance_and_license_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            output = Path(temporary) / "output"
            source.mkdir()
            output.mkdir()
            (source / "LICENSE").write_text("upstream license")
            (source / "Cargo.toml").write_text('[workspace.package]\nversion="0.6.15"\n')
            (source / "Cargo.lock").write_text("locked")
            dependency = source / "dependency"
            dependency.mkdir()
            (dependency / "LICENSE-MIT").write_text("dependency license")
            (output / "cargo-metadata.json").write_text(json.dumps({"packages": [{
                "name": "example",
                "version": "1.0.0",
                "manifest_path": str(dependency / "Cargo.toml"),
                "license": "MIT",
                "source": "registry+fixture",
            }, {
                "name": "cli",
                "version": "0.6.15",
                "manifest_path": str(source / "Cargo.toml"),
                "license": "MIT",
                "source": None,
                "features": {"default": ["cpu", "metal"]},
            }]}))

            def command(*args, cwd=None):
                if args[:2] == ("git", "status"):
                    return ""
                return "recorded-input"

            with patch.object(packager, "command", side_effect=command):
                packager.package_info(source, output)
            info = json.loads((output / "BUILD-INFO.json").read_text())
            self.assertEqual(info["source_version"], "0.6.15")
            self.assertEqual(info["source_sha"], "recorded-input")
            self.assertEqual(info["target"], "aarch64-apple-darwin")
            self.assertEqual(info["cargo_lock_sha256"], hashlib.sha256(b"locked").hexdigest())
            self.assertEqual((output / "licenses/example-1.0.0/LICENSE-MIT").read_text(), "dependency license")
            self.assertEqual((output / "LICENSE-UZU").read_text(), "upstream license")
            notices = json.loads((output / "THIRD-PARTY.json").read_text())
            self.assertTrue(all(notice["license"] == "MIT" for notice in notices))
            self.assertEqual(info["features"], ["cpu", "metal"])


class ConsumerContractTests(unittest.TestCase):
    def test_catalog_identifiers_and_folders_bypass_slash_matching(self):
        models = (ROOT / "uzu/Project/Sources/Classes/_models.4dm").read_text()
        delegation = models.split("If (Not:C34(This:C1470.offline))")[0]
        self.assertIn("This:C1470.options.model#\"\"", delegation)
        self.assertIn("4D:C1709.Folder", delegation)
        self.assertNotIn("Match regex", delegation)

    def test_termination_handle_and_persistent_cache(self):
        public = (ROOT / "uzu/Project/Sources/Classes/uzu.4dm").read_text()
        self.assertIn("Count parameters:C259=0", public)
        server = (ROOT / "uzu/Project/Sources/Classes/_server.4dm").read_text()
        self.assertNotIn("HF_HUB_CACHE", server)
        self.assertNotIn("Generate UUID", server)
        self.assertIn('$command+=" server "', server)
        self.assertIn('"onTerminate"; "onStdErr"; "onStdOut"', server)

    def test_obsolete_router_paths_removed_and_model_errors_explicit(self):
        startup = (ROOT / "uzu/Project/Sources/Methods/start.4dm").read_text()
        self.assertNotIn("models_preset", startup)
        self.assertNotIn("models_dir", startup)
        self.assertIn("Uzu requires options.model", startup)
        self.assertIn("onError.call", startup)
        self.assertIn("LOG EVENT", startup)

    def test_documentation_relative_links_exist(self):
        import re
        import urllib.parse
        files = [ROOT / "README.md", *list((ROOT / "docs").glob("*.md")),
                 *list((ROOT / "uzu/Documentation").rglob("*.md")),
                 ROOT / "uzu/Resources/bin/macOS/README.md"]
        for file in files:
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", file.read_text()):
                url = urllib.parse.urlsplit(link)
                if not url.scheme and url.path:
                    with self.subTest(file=file, link=link):
                        self.assertTrue((file.parent / urllib.parse.unquote(url.path)).exists())


if __name__ == "__main__":
    unittest.main()
