# uzu

Public entry point for the native `cli server` process.

> uzu.new (port : Integer; huggingfaces : cs.event.huggingfaces; HOME : 4D.Folder; options : Object; event : cs.event.event)

| Parameter | Type | Description |
| --- | --- | --- |
| port | Integer | Listening port; invalid/zero defaults to 8080 |
| huggingfaces | cs.event.huggingfaces | Legacy component-managed downloads; `Null` defaults to an empty collection |
| HOME | 4D.Folder | Component working/download folder; defaults to `~/.uzu` if absent or nonexistent; does not change Uzu's model cache |
| options | Object | Valid `cli server` flags; see below |
| event | cs.event.event | Startup/download/process callbacks |

Requires 4D v20 R-series+ and a native Apple Silicon server on macOS 26.4+.
Install `cli` at `/RESOURCES/bin/macOS/cli` or on `PATH`.
See [native builds](../../../docs/native-builds.md) for artifacts and requirements.

## Options

| Property | Type | Meaning |
| --- | --- | --- |
| model | Text or existing 4D.Folder | Catalog identifier, supported repository ID, or complete Uzu-compatible local directory |
| host | Text | Bind address; default `127.0.0.1` |
| port | Integer | Set from the constructor's first argument |
| prefix_cache | Boolean | Explicitly enable prefix cache (already the upstream default) |
| no_prefix_cache | Boolean | Disable prefix cache; mutually exclusive with `prefix_cache` |
| verbose_file_log | Boolean | Verbose server file logging |

Underscores become hyphens; true booleans emit switches. Unknown flags are
rejected by upstream. `max_tokens` is a chat-request field, not a server flag.
GGUF files, router INI files, `embeddings`, GPU-layer options and llama.cpp
sampling flags are **not supported** by this server command.

Prefer passing `model` directly and letting Uzu resolve/download it. Legacy
`huggingfaces` descriptors are useful only when they download a complete,
correctly structured Uzu model directory. They are not a GGUF import path.

## Example

```4d
var $event : cs.event.event
$event:=cs.event.event.new()
$event.onError:=Formula(ALERT($2.message))

var $uzu : cs.uzu.uzu
$uzu:=cs.uzu.uzu.new(8080; Null; Folder(fk home folder).folder(".uzu"); \
    {model: "alibaba:qwen3.5:0.8b:mirai:mirai-m:4"; host: "127.0.0.1"}; $event)
```

Non-empty text identifiers (including colon-separated catalog IDs) and existing
`4D.Folder` models are delegated immediately to the native CLI. Uzu stores its
downloads in its own persistent cache, currently `~/.cache/mirai`.

The constructor checks for an existing managed worker; it does not start another
for the same port. The TCP preflight reports another process occupying the port
through `onError`. Missing model options are reported through `onError`, or the
4D debug log if no event object is provided.

If legacy `huggingfaces` descriptors resolve no files (nothing to download),
the server starts only when `options.model` is an existing local `4D.Folder`;
otherwise `onError` receives code `2` (naming the folder path when one was
given) and nothing is launched. The server is launched at most once per
attempt. `event` may be `Null`; no callbacks are then delivered.

`onSuccess(options; models)` currently signals **worker launch**, not HTTP
readiness. Model loading/download may still be running; poll `/v1/models`.
For identifier models, the event's model list is a placeholder rather than a
native catalog response. `onData`/`onResponse` refer to component-managed file
downloads, not Uzu's own internal downloads. `onTerminate(worker; params)` reports
process exit. The server's stdout/stderr are intentionally not forwarded
(`onStdOut`/`onStdErr` are not bound): a long-running server can produce a
large amount of output.

To terminate (including from `onExit`):

```4d
var $uzu : cs.uzu.uzu
$uzu:=cs.uzu.uzu.new()
$uzu.terminate()
```

The no-argument constructor is the existing termination-handle idiom, not a
way to start an unspecified default model.

## See also

- [`_interface`](_interface.md): TCP check and termination
- [`_models`](_models.md), [`_Model`](_Model.md): model/download lifecycle
- [`_server`](_server.md): native command construction
