# Uzu for 4D

Run [Uzu](https://github.com/trymirai/uzu)'s native inference server from a 4D application. This repository provides the 4D process-lifecycle component, **source-built native server release workflows**, and a separate [documentation site](https://miyako.github.io/uzu/).

[Documentation](https://miyako.github.io/uzu/) · [Releases](https://github.com/miyako/uzu/releases) · [Native build/release guide](docs/native-builds.md) · [4D class reference](uzu/Documentation/Classes/uzu.md)

## Supported configuration

| Requirement | Support |
| --- | --- |
| Native server | Apple Silicon (`arm64`), macOS **26.4+**, Apple GPU |
| 4D component | 4D v20 R-series or later, running natively on Apple Silicon; `tcp`, `workers`, `event` dependencies declared in the project |
| Model input | Uzu catalog identifier, supported Hugging Face repository ID, or complete Uzu-compatible local **directory** |
| HTTP API | `/v1/models`, `/v1/chat/completions`; decision-model endpoints depend on the selected model |

No Intel, Windows or Linux server releases are promised. A compilable Intel slice is not evidence of usable inference: the upstream default Metal backend requires an Apple GPU. There is no GGUF loader, llama.cpp router mode, embeddings endpoint, image-generation API or files API in this server CLI.

The current upstream workspace is `0.6.15`. The reviewed source revision is [`798803bba8fc26b2afd61e9a8ae23ab9c16d3994`](https://github.com/trymirai/uzu/commit/798803bba8fc26b2afd61e9a8ae23ab9c16d3994); each actual release records **its own resolved SHA** in `BUILD-INFO.json`. Official upstream `mirai` release archives are not a substitute for the `cli server` command used here.

## Install and run

Choose a **`server-*` native release** from [Releases](https://github.com/miyako/uzu/releases), not a 4D component version. Download the notarized `uzu-server-macos-arm64.dmg`, or the signed `uzu-server-macos-arm64.tar.gz`, with `SHA256SUMS`. Verify the downloaded file against its checksum. The DMG has a stapled offline notarization ticket; the tar's signed executable may require network access for Gatekeeper verification.

```sh
tar -xzf uzu-server-macos-arm64.tar.gz
cd uzu-server-macos-arm64
./cli --version
./cli server --help
./cli server --model alibaba:qwen3.5:0.8b:mirai:mirai-m:4 --host 127.0.0.1 --port 8080
```

In another terminal, wait for the model to load before requesting completions:

```sh
curl --fail http://127.0.0.1:8080/v1/models
curl --fail http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"alibaba:qwen3.5:0.8b:mirai:mirai-m:4","messages":[{"role":"user","content":"Hello"}],"max_tokens":64}'
```

Models are downloaded separately on first use; access, memory requirements and licenses vary. Keep `127.0.0.1` unless you deliberately provide a protected network boundary: this server does not supply API authentication. No Rust, Homebrew, external `.metallib` or non-system dylib is needed to run packaged native releases.

### Use from 4D

Published 4D components receive a verified native release during packaging. A **source checkout does not bundle executables**: install `cli` and its accompanying build information/licenses from a native archive into `uzu/Resources/bin/macOS/`. The exact executable path is `uzu/Resources/bin/macOS/cli`; if absent, the launcher falls back to `cli` on `PATH`. Old checked-in universal executables and the developer-only `cli-tools` are no longer shipped.

Add the project as a 4D component, then start with a model identifier:

```4d
var $event : cs.event.event
$event:=cs.event.event.new()
$event.onError:=Formula(ALERT($2.message))

var $uzu : cs.uzu.uzu
var $homeFolder : 4D.Folder
$homeFolder:=Folder(fk home folder).folder(".uzu")
$uzu:=cs.uzu.uzu.new(8080; Null; $homeFolder; \
    {model: "alibaba:qwen3.5:0.8b:mirai:mirai-m:4"; host: "127.0.0.1"}; $event)
```

The first parameter sets `--port`; option underscores become hyphens. Supported server options are `model`, `host`, `port`, `prefix_cache`, `no_prefix_cache`, and `verbose_file_log`. `max_tokens` belongs in the **HTTP request**, not the server options. Pass an existing `4D.Folder` as `model` for a complete compatible local model directory, not an individual weights/GGUF file.

`onSuccess` currently means the worker was started, **not** that model download or HTTP readiness is complete. Poll `/v1/models` before sending requests. For identifiers, the component's model event is a placeholder; query the endpoint for the actual loaded model. Model storage uses Uzu's own cache (currently `~/.cache/mirai`); the 4D `HOME` argument does not relocate it. Legacy component-managed Hugging Face downloads remain available only for complete, correctly structured Uzu model directories; letting Uzu resolve/download models is recommended.

If legacy `huggingfaces` descriptors resolve no files, the server starts only when `options.model` is an existing local `4D.Folder`; otherwise `event.onError` receives an error with code `2`, whose message says why each descriptor was skipped (for example the HTTP status returned by Hugging Face), and nothing is launched. If the Hugging Face API is unreachable and the descriptor's local folder does not exist, `event.onError` also receives code `2` instead of the server being started without `--model`. The server is launched at most once per wrapper attempt. `event` may be `Null`, in which case no callbacks are delivered. stdout/stderr of the server are intentionally not forwarded.

To terminate in `onExit`:

```4d
var $uzu : cs.uzu.uzu
$uzu:=cs.uzu.uzu.new()
$uzu.terminate()
```

## Build and update

**Actions → Update server** defaults to upstream `main` HEAD: “latest” means latest **source**, not latest GitHub release. The workflow resolves the ref once, records the full SHA and Cargo lockfile hash, and builds `cargo build --locked --release --package cli --target aarch64-apple-darwin` with a dated nightly. Default/PR runs upload clearly named **unsigned build artifacts without Apple credentials**. Select `publish_release` on the default branch to sign, notarize and publish native assets. No release is published merely by merging these workflow changes.

Native tags contain upstream version, source SHA prefix and run identity; they do not change the component's semantic version or GitHub's “latest” component release. Optional `publish_component` passes that exact native release tag to **Publish**. Standalone Publish accepts `server_tag`; empty selects the newest complete native release and records its resolved identity. It fails instead of silently bundling a stale executable when no release exists.

See [native-builds.md](docs/native-builds.md) for prerequisites, reproduction, smoke tests, runner limitations, signing secrets, dependency notices and required repository/Pages settings.

## Attribution and licenses

[Uzu / Mirai Tech Inc.](https://github.com/trymirai/uzu) provides the inference engine and native CLI under [MIT](https://github.com/trymirai/uzu/blob/main/LICENSE). This repository's 4D integration and site are [MIT](LICENSE). Native archives carry `LICENSE-UZU`, `LICENSE-COMPONENT`, `THIRD-PARTY.json`, and available dependency license/notice files. Model licenses are separate and models are not redistributed. The site takes layout/deployment inspiration from [miyako/llama-cpp](https://github.com/miyako/llama-cpp); it does not inherit that engine's platform or API support.
