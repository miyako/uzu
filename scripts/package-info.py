"""Record exact native build inputs and redistribute available dependency notices."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib


def command(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def package_info(source, output):
    metadata = json.loads((output / "cargo-metadata.json").read_text())
    manifest = tomllib.loads((source / "Cargo.toml").read_text())
    shutil.copyfile(source / "LICENSE", output / "LICENSE-UZU")
    root = Path(__file__).resolve().parents[1]
    shutil.copyfile(root / "LICENSE", output / "LICENSE-COMPONENT")
    shutil.copyfile(root / "docs/native-install.txt", output / "README.txt")
    packages = []
    for package in sorted(metadata["packages"], key=lambda item: (item["name"], item["version"])):
        package_root = Path(package["manifest_path"]).parent
        notices = []
        candidates = set()
        for pattern in ("LICENSE*", "LICENCE*", "NOTICE*", "COPYING*"):
            candidates.update(package_root.rglob(pattern))
        if package.get("license_file"):
            candidates.add(package_root / package["license_file"])
        for notice in sorted(candidates):
            if notice.is_file():
                relative = notice.relative_to(package_root) if notice.is_relative_to(package_root) else Path(notice.name)
                destination = output / "licenses" / f'{package["name"]}-{package["version"]}' / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(notice, destination)
                notices.append(str(destination.relative_to(output)))
        packages.append({
            "name": package["name"],
            "version": package["version"],
            "license": package["license"],
            "source": package["source"],
            "notices": notices,
        })
    (output / "THIRD-PARTY.json").write_text(json.dumps(packages, indent=2) + "\n")
    info = {
        "source_repository": "https://github.com/trymirai/uzu",
        "requested_ref": os.environ.get("SOURCE_REF", "local checkout"),
        "source_sha": command("git", "rev-parse", "HEAD", cwd=source),
        "source_dirty": bool(command("git", "status", "--porcelain", cwd=source)),
        "source_version": manifest["workspace"]["package"]["version"],
        "packaging_sha": command("git", "rev-parse", "HEAD", cwd=root),
        "packaging_dirty": bool(command("git", "status", "--porcelain", cwd=root)),
        "cargo_lock_sha256": hashlib.sha256((source / "Cargo.lock").read_bytes()).hexdigest(),
        "rust_toolchain": os.environ.get("RUST_TOOLCHAIN", "nightly-2026-08-10"),
        "rustc": command("rustc", "+" + os.environ.get("RUST_TOOLCHAIN", "nightly-2026-08-10"), "-Vv"),
        "xcode": command("xcodebuild", "-version"),
        "sdk": command("xcrun", "--sdk", "macosx", "--show-sdk-version"),
        "metal": command("xcrun", "--sdk", "macosx", "metal", "--version"),
        "target": "aarch64-apple-darwin",
        "minimum_macos": os.environ.get("MACOSX_DEPLOYMENT_TARGET", "26.4"),
        "cargo_command": "cargo build --locked --release --package cli --target aarch64-apple-darwin",
        "features": next(package.get("features", {}).get("default", [])
                         for package in metadata["packages"] if package["name"] == "cli"),
    }
    if info["source_dirty"]:
        raise RuntimeError("Refusing to package modified upstream source")
    (output / "BUILD-INFO.json").write_text(json.dumps(info, indent=2) + "\n")


if __name__ == "__main__":
    package_info(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
