# Native Uzu server builds and releases

## What is actually built

Upstream was inspected at [`798803bba8fc26b2afd61e9a8ae23ab9c16d3994`](https://github.com/trymirai/uzu/tree/798803bba8fc26b2afd61e9a8ae23ab9c16d3994), workspace version `0.6.15`, on 2026-11-02. Its latest official release at that time was `0.6.15` (2026-10-30), with `mirai` GUI/desktop archives rather than this server binary. These are different products:

| Upstream source | Evidence / consequence |
| --- | --- |
| `Cargo.toml`, `crates/legacy/cli/Cargo.toml` | Package and binary are both `cli`, default features `cpu,metal`; build this package, not the GUI |
| `crates/legacy/cli/src/main.rs` | `cli server` takes `--model`, `--host`, `--port`, prefix-cache switches and `--verbose-file-log`; no server `--max-tokens` |
| `crates/legacy/cli/src/server/runner.rs` | Models/chat routes, streaming chat handler, model-specialized decisions; defaults to loopback |
| `crates/legacy/uzu/src/engine/mod.rs` | Accepts model identifiers, repository IDs and compatible local directories |
| `crates/uzu-engine/build/metal/toolchain.rs` | Metal **4.0**, minimum OS **26.4**, Xcode Metal compiler required |
| `crates/uzu-engine/src/backends/metal/metal_extensions/device_extensions.rs` | Explicitly requires an **Apple GPU** |
| `crates/uzu-engine/build/metal/compiler.rs` | Compiled shaders embedded with `include_bytes!`; do not invent a separate runtime metallib asset |
| `crates/legacy/uzu/src/storage/storage.rs` | Persistent model cache under device home `.cache/mirai`; arbitrary `HF_HUB_CACHE` overrides do not relocate it |
| `rust-toolchain.toml`, workspace `rust-version` | Upstream requests floating nightly; workspace minimum Rust `1.98` |

The release target is **`aarch64-apple-darwin` only**, native Apple Silicon on macOS 26.4+. CPU/WebGPU backends and upstream multi-platform library/binding targets are not proof that this repository can ship a working Intel/Windows/Linux Metal server. In particular, producing two Mach-O slices and passing `--help` does not exercise GPU inference. No universal server is published.

## Selection and reproducibility

Run **Actions → Update server**. `source_ref` defaults to `main` in **trymirai/uzu**, so “latest” means upstream default-branch source HEAD at checkout time, **not** the latest release tag. A tag or full SHA may be supplied instead. The workflow never falls back to an old release or downloads a prebuilt upstream binary.

The one checkout is built without patching. `cargo --locked` refuses dependency resolution changes. `BUILD-INFO.json` records the full upstream SHA, requested ref, workspace version, Cargo.lock SHA-256, packaging repository SHA/dirty state, exact `rustc -Vv`, dated toolchain, Xcode/SDK/Metal versions, deployment target, target triple and build command. Git dependencies are resolved by the upstream lockfile. Source changes detected before packaging are rejected.

The default compiler is **`nightly-2026-08-10`** (`rustc 1.99.0-nightly`, commit `969b803cb`, 2026-08-09), a verified dated toolchain satisfying the reviewed workspace. A future upstream update may require another dated nightly or Xcode version; select it explicitly and do not weaken upstream's minimum version or silently edit its code to force a build. Binary reproducibility is not claimed: Xcode runner images, code-signing timestamps and notarization are external inputs, recorded where possible.

## Credential-free build

On an Apple Silicon Mac with macOS 26.4+, full Xcode including a Metal 4-capable toolchain, Rustup, CMake, Git and Python 3.12+:

```sh
git clone https://github.com/trymirai/uzu.git .upstream
git -C .upstream checkout 798803bba8fc26b2afd61e9a8ae23ab9c16d3994
rustup toolchain install nightly-2026-08-10 --profile minimal --target aarch64-apple-darwin
xcodebuild -downloadComponent MetalToolchain
export RUST_TOOLCHAIN=nightly-2026-08-10
export MACOSX_DEPLOYMENT_TARGET=26.4
export SOURCE_REF=798803bba8fc26b2afd61e9a8ae23ab9c16d3994
bash scripts/build-native.sh .upstream dist/uzu-server-macos-arm64
```

The script builds **only** the server package, checks the arm64 architecture and Mach-O minimum OS (26.4), runs `--version`/`server --help`, verifies required options, requires Clap's usage-error exit code for the obsolete `server --max-tokens` invocation, and rejects non-system dylib dependencies reported by `otool -L`. It also records build metadata and dependency licenses. Cargo registry/git downloads are cached in Actions; compiled Metal outputs are not reused across Xcode/SDK changes.

Normal workflow dispatch defaults to **build only** (`publish_release: false`). Pull requests changing the native build pipeline also build/test without secrets. The `native-server-unsigned` Actions artifact contains `uzu-server-unsigned-macos-arm64.tar.gz`; it is **not a signed/notarized distribution**. It preserves executable permissions inside a tar rather than relying on artifact ZIP metadata. Apple credentials are never needed for local source builds, PR tests or site validation.

Hosted build jobs use `macos-26`, assert `arm64`, provision the Metal toolchain, and have a 120-minute timeout. A macOS runner label alone does not guarantee its current Xcode/Metal SDK supports 26.4: explicit toolchain/build checks fail if insufficient. A model-free help check cannot validate Metal execution. For inference, on suitable hardware run the command in [native-install.txt](native-install.txt), wait for `/v1/models`, then send a chat completion. Models/network, disk and unified memory are needed; use Uzu-compatible model directories, not GGUF files.

An optional real-model check starts its own loopback server, waits for a non-empty
model list, verifies an assistant completion with generated tokens, and terminates
only its own child process:

```sh
python3 scripts/smoke-inference.py dist/uzu-server-macos-arm64/cli \
  --model alibaba:qwen3.5:0.8b:mirai:mirai-m:4
```

This can download model weights into Uzu's normal cache. It is not run on hosted
CI: compiling Metal or showing CLI help does not demonstrate that a hosted VM
exposes an Apple GPU. Use a real supported Mac for inference testing.

An existing cached catalog/partial checkpoint can fail at session creation with
`Backend error: I/O error: No such file or directory`, even though the same model
ID works with a fresh cache. This was reproduced locally with the reviewed
revision; an isolated fresh cache successfully served models and generated chat
tokens on an M1 Pro. The upstream server's download loop does not validate the
terminal download phase before creating the session. Preserve the failing
checkpoint/catalog details for an upstream report rather than deleting an
existing user cache automatically. A complete compatible local model directory
is another supported input. This repository does not patch upstream's downloader.

## Explicit publication

Only a default-branch manual run with **`publish_release: true`** enters the signing job. It imports the existing repository signing credentials, resolves exactly one Developer ID Application identity for the configured team, signs the executable with hardened runtime/timestamp, verifies its signature and CLI again, creates/signs a DMG, and submits it to Apple's notary service. Only **Accepted** submissions proceed; failure retrieves the notarization log. The DMG is stapled, validated and assessed with Gatekeeper before publication.

Native tags use `server-<upstream-version>-<12-character-source-sha>-<run-id>-<attempt>` to avoid overwriting releases or confusing upstream and component versions. Release tags point to the packaging commit; upstream provenance lives in `BUILD-INFO.json`. Native releases use `--latest=false`, leaving the existing 4D component “latest” release unchanged. No branch push, binary commit or version bump is performed by the native workflow.

| Asset | Contents / use |
| --- | --- |
| `uzu-server-macos-arm64.dmg` | Signed server, notices, build information; stapled offline ticket |
| `uzu-server-macos-arm64.tar.gz` | Same signed executable and documentation, root `uzu-server-macos-arm64/`; tar cannot carry a stapled ticket |
| `BUILD-INFO.json` | Independently downloadable provenance |
| `SHA256SUMS` | SHA-256 of DMG, tar archive and provenance |

The archive root contains `cli`, `README.txt`, `LICENSE-UZU`, `LICENSE-COMPONENT`, `BUILD-INFO.json`, `THIRD-PARTY.json`, and `licenses/`. Dependency metadata/notices conservatively cover the resolved Cargo workspace, including build-time dependencies; this is not a minimal linked-dependency report. `cli-tools` is an upstream developer utility, unnecessary to run the server, and is not included. Native CLI runtime dependencies are Apple system libraries/frameworks only; the smoke check fails on Homebrew paths, `@rpath` and other unbundled libraries.

Download assets from the **same release**. With all three files present:

```sh
shasum -a 256 --check SHA256SUMS
```

If downloading just the tar or DMG, verify that file against its line in `SHA256SUMS` (a full check will correctly report missing other files). Keep license/notice files with redistributed executables. Upstream and this integration use MIT; dependency and model licenses remain their own.

### Signing secrets

Reuse the existing **Publish** secret conventions:

| Secret | Purpose |
| --- | --- |
| `APPLE_DEVELOPER_ID_CERTIFICATE` | Base64-encoded Developer ID Application `.p12` |
| `APPLE_DEVELOPER_ID_CERTIFICATE_PASSWORD` | Certificate import password |
| `KEYCHAIN_PASSWORD` | Temporary signing keychain |
| `NOTARYTOOL_APPLE_ID` | Apple account |
| `NOTARYTOOL_TEAM_ID` | Apple Developer team |
| `NOTARYTOOL_PASSWORD` | App-specific notarization password |

No separate signing identity secret is needed. Signing credentials are cleaned up even on failure. Native publication requires `contents: write` only in its release job; build/sign jobs have read-only repository access. Do not copy secrets into source or artifact metadata.

## 4D component publishing

The optional `publish_component` input runs the existing reusable **Publish** workflow after the native release, forwarding its **exact tag**. Standalone Publish accepts `server_tag`; when empty, `scripts/install-native.py` resolves the newest non-draft/non-prerelease `server-*` release with all required assets. It verifies tar/provenance checksums, target and source SHA, safely extracts the archive, checks the restored CLI and installs it at `uzu/Resources/bin/macOS/cli` before building the 4D component. The component includes the native notices/provenance. No existing release means a clear failure, not a component with an absent or old CLI.

The old tracked universal `cli`/`cli-tools` are removed. A source checkout must install a native release manually or build locally; `/RESOURCES/bin/macOS/cli` and the `cli` PATH fallback remain compatible. Generated native files are ignored, so the existing npm component-version action does not commit binaries. Component semver and signing remain separate from upstream/native versions. The existing self-hosted option applies only to component publishing; that host must now be Apple Silicon with macOS 26.4+.

The component's generic argument conversion is retained, but upstream determines valid flags. Startup now delegates **all non-empty identifiers** (including colon-separated catalog IDs) and existing `4D.Folder` models directly to Uzu; the old slash-only test left them stuck without launching. Legacy Hugging Face download descriptors must resolve a complete Uzu directory. Router-only startup paths were removed because the server does not support router flags. No temporary `HF_HUB_CACHE` directory is created: the current upstream storage does not use it.

## Repository settings and validation

- Enable Actions; allow read access for build/download jobs and `contents: write` for native/component releases. Existing component semver actions also need permission to push version commits/tags to the default branch, subject to repository rules.
- Configure **Settings → Pages → Source → GitHub Actions**. The Pages workflow builds only `site/` and deploys a Pages artifact. Project-base links target `/uzu/`; README is not the website source.
- Provision the Apple secrets above only if publishing. First publish a native release before standalone component publishing. Build-only runs and Pages need no Apple secrets.
- No remote settings, release execution or branch-rule changes are performed by this implementation.

Local checks:

```sh
python3 -m unittest discover -s tests -v
python3 site/build.py --base-path /uzu/
bash -n scripts/build-native.sh scripts/smoke-native.sh
actionlint
git diff --check
```

GitHub runners, secrets, Apple notarization and Pages deployment can only be verified by authorized remote runs. A successful local source build or unsigned Actions artifact must not be described as a published/notarized release or a passing GitHub CI run.

`tests/4d/validate.4dm` is a native 4D regression method for catalog/repository IDs,
existing local-folder delegation, the no-argument termination handle, a `Null`
event, `onError` code 2 when nothing is downloaded and no local folder is given
or when starting with a nonexistent model folder,
and locale-independent numeric arguments. To run
it, copy `uzu/` into a disposable project directory, install the declared `tcp`,
`workers` and `event` components in its `Components/`, copy the method into
`Project/Sources/Methods/validate.4dm`, and invoke Tool4D with
`--skip-onstartup --dataless --startup-method=validate`. Check the resulting
`regressions.json` for `success: true` and an empty failure list. The Python
consumer-contract tests are supplementary source checks, not a 4D compiler.
