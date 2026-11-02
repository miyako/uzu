#!/bin/bash
set -euo pipefail

source_dir=${1:?Usage: build-native.sh upstream-directory output-directory}
output_dir=${2:?Usage: build-native.sh upstream-directory output-directory}
script_dir=$(cd "$(dirname "$0")" && pwd)
source_dir=$(cd "$source_dir" && pwd)
mkdir -p "$output_dir"
output_dir=$(cd "$output_dir" && pwd)
export MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET:-26.4}
export RUST_TOOLCHAIN=${RUST_TOOLCHAIN:-nightly-2026-08-10}
test "$(uname -m)" = arm64
test -f "$source_dir/Cargo.lock"

(
  cd "$source_dir"
  # cli is the server; neither the Mirai GUI release nor cli-tools replaces it.
  cargo "+$RUST_TOOLCHAIN" build --locked --release --package cli --target aarch64-apple-darwin
  cargo "+$RUST_TOOLCHAIN" metadata --locked --format-version 1 \
    --filter-platform aarch64-apple-darwin > "$output_dir/cargo-metadata.json"
)
cp "$source_dir/target/aarch64-apple-darwin/release/cli" "$output_dir/cli"
chmod 755 "$output_dir/cli"
bash "$script_dir/smoke-native.sh" "$output_dir/cli"
python3 "$script_dir/package-info.py" "$source_dir" "$output_dir"
rm "$output_dir/cargo-metadata.json"
