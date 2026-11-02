#!/bin/bash
set -euo pipefail

binary=${1:?Usage: smoke-native.sh /path/to/cli}
test -x "$binary"
test "$(lipo -archs "$binary")" = arm64
test "$(xcrun vtool -show-build "$binary" | awk '/minos/ {print $2}')" = 26.4
"$binary" --version
help=$("$binary" server --help)
printf '%s\n' "$help"
for option in --model --host --port --no-prefix-cache --verbose-file-log; do
  grep -Fq -- "$option" <<< "$help"
done
if invalid_output=$("$binary" server --model unused --max-tokens 1 2>&1); then
  echo "Unexpected server CLI: --max-tokens should be a request option, not a server flag" >&2
  exit 1
else
  status=$?
  test "$status" -eq 2
  grep -Fq 'unexpected argument' <<< "$invalid_output"
  grep -Fq -- '--max-tokens' <<< "$invalid_output"
fi

# Fail on Homebrew, build-tree, @rpath or other non-system dylib dependencies.
otool -L "$binary"
otool -L "$binary" | tail -n +2 | awk '{print $1}' |
  while IFS= read -r dependency; do
    case "$dependency" in
      /System/Library/*|/usr/lib/*) ;;
      *) echo "Unpackaged runtime dependency: $dependency" >&2; exit 1 ;;
    esac
  done
