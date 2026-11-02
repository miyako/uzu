"""Install a checksummed native server release into the component before packaging."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile


ARCHIVE = "uzu-server-macos-arm64.tar.gz"
REQUIRED_ASSETS = {ARCHIVE, "SHA256SUMS", "BUILD-INFO.json"}


def select_release(pages):
    for page in pages:
        for release in page:
            if (
                release["tag_name"].startswith("server-")
                and not release["draft"]
                and not release["prerelease"]
                and REQUIRED_ASSETS.issubset({asset["name"] for asset in release["assets"]})
            ):
                return release["tag_name"]
    raise RuntimeError("No complete native server release; run Update server first")


def verify_checksum(directory, filename):
    lines = (directory / "SHA256SUMS").read_text().splitlines()
    hashes = [line.split()[0] for line in lines if line.split()[-1].lstrip("*") == filename]
    if len(hashes) != 1 or not re.fullmatch(r"[a-f0-9]{64}", hashes[0]):
        raise RuntimeError(f"Missing or ambiguous checksum for {filename}")
    actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
    if actual != hashes[0]:
        raise RuntimeError(f"Checksum mismatch: {filename}")


def install():
    repository = os.environ["GH_REPO"]
    tag = os.environ.get("SERVER_TAG", "")
    if not tag:
        pages = json.loads(subprocess.check_output(
            ["gh", "api", f"repos/{repository}/releases?per_page=100", "--paginate", "--slurp"],
            text=True,
        ))
        tag = select_release(pages)
    if not re.fullmatch(r"server-[A-Za-z0-9.+-]+", tag):
        raise ValueError(f"Not a native server release tag: {tag}")
    destination = Path("uzu/Resources/bin/macOS")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="uzu-native-") as temporary:
        directory = Path(temporary)
        subprocess.run(
            ["gh", "release", "download", tag, "--repo", repository, "--dir", temporary,
             "--pattern", ARCHIVE, "--pattern", "SHA256SUMS", "--pattern", "BUILD-INFO.json"],
            check=True,
        )
        for filename in (ARCHIVE, "BUILD-INFO.json"):
            verify_checksum(directory, filename)
        info = json.loads((directory / "BUILD-INFO.json").read_text())
        if info["target"] != "aarch64-apple-darwin" or not re.fullmatch(r"[a-f0-9]{40}", info["source_sha"]):
            raise RuntimeError("Unexpected native build target or source revision")
        with tarfile.open(directory / ARCHIVE) as archive:
            archive.extractall(directory / "unpacked", filter="data")
        payload = directory / "unpacked/uzu-server-macos-arm64"
        if (payload / "BUILD-INFO.json").read_bytes() != (directory / "BUILD-INFO.json").read_bytes():
            raise RuntimeError("Archive provenance does not match release provenance")
        subprocess.run(["bash", "scripts/smoke-native.sh", str(payload / "cli")], check=True)
        shutil.copytree(payload, destination, dirs_exist_ok=True)
    summary = f"Native server: {repository}@{tag}\nUpstream source: {info['source_sha']}\n"
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as output:
            output.write(summary)


if __name__ == "__main__":
    install()
