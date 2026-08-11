# uzu
Local inference engine

[Uzu](https://github.com/trymirai/uzu) is a high-performance inference engine for AI models. It allows you to deploy AI directly in your app with zero latency, full data privacy, and no inference costs.

This 4D component manages the process lifecycle: resolving models (either a Hugging Face repo, which `uzu` itself downloads, or local Hugging Face assets fetched by the component), building the `cli server` command line, launching it as a background process, and shutting it down cleanly when the app quits.

## Requirements

- 4D v20 R-series or later (uses 4D classes, `4D.SystemWorker`, `4D.HTTPRequest`, formulas, etc.)
- The `uzu` command-line executable, placed at:

  ```
  /RESOURCES/bin/{platform}/cli
  ```

  If the binary isn't found there, the component falls back to calling `cli` from `$PATH`. On macOS the component `chmod +x`'s the binary on first use.

## What's included

| File | Role |
|---|---|
| `uzu.4dm` | Public entry point. Checks the requested port isn't already in use, fills in sensible defaults, and starts the server via a 4D worker. |
| `_interface.4dm` | Shared constructor/`terminate()` contract, plus the TCP pre-flight check (`_onTCP`) that reports a port conflict through the `event.onError` callback. |
| `_CLI.4dm` | Generic wrapper around a native command-line executable: locates the binary, escapes arguments for bash/zsh or cmd.exe, and resolves the current directory. |
| `_CLI_Controller.4dm` | Generic controller that drives a `4D.SystemWorker`: queues commands, wires up `onData` / `onDataError` / `onResponse` / `onError` / `onTerminate`, and manages worker lifecycle. |
| `_uzu.4dm` / `_uzu_Controller.4dm` | uzu-specific specializations of `_CLI` / `_CLI_Controller` (executable name `cli`, `port` property, termination pass-through). |
| `_server.4dm` | Builds the actual `cli server` command line from an options object (flags derived from key/value pairs) and starts it as a system worker. |
| `_models.4dm` / `_Model.4dm` | Resolves the model reference. If `options.model` is a Hugging Face repo id (plain text, e.g. `"trymirai/Qwen3.5-0.8B-L"`), it's passed straight through to `cli` and **uzu downloads it itself**. If Hugging Face assets are listed via `huggingfaces`, the component resolves and downloads them itself instead, then calls `start()` once everything is on disk. |
| `onStartup.4dm` | Example database method: starts `uzu` with a Hugging Face model id when the 4D app launches. |
| `onExit.4dm` | Terminates the running `uzu` worker when the 4D app quits. |

## Installation

1. Add this project as a 4D component (or copy it into `Components/` of your host database).
2. Build or download the `uzu` CLI binary from [trymirai/uzu](https://github.com/trymirai/uzu) and place it at `RESOURCES/bin/{platform}/cli` in your project.
3. Call `cs.uzu.uzu.new(...)` from `onStartup` (see below), and `cs.uzu.new().terminate()` from `onExit`.

## Basic usage

```4d
var $uzu : cs.uzu.uzu
var $homeFolder : 4D.Folder
$homeFolder:=Folder(fk home folder).folder(".uzu")

var $event : cs.event.event
$event:=cs.event.event.new()
$event.onError:=Formula(ALERT($2.message))

var $port : Integer
$port:=8080

var $options : Object
$options:={model: "trymirai/Qwen3.5-0.8B-L"; port: $port}

var $huggingfaces : cs.event.huggingfaces
$huggingfaces:=cs.event.huggingfaces.new([])  //empty: let uzu handle the download itself

$uzu:=cs.cs..uzu.new($port; $huggingfaces; $homeFolder; $options; $event)
```

On termination (e.g. in `onExit`):

```4d
var $uzu : cs.uzu.uzu
$uzu:=cs.uzu.uzu.new()
$uzu.terminate()
```

### How it starts up

1. `uzu.new(...)` checks whether the given port is already bound; if so, `event.onError` fires and nothing else happens.
2. Model resolution then follows one of two paths:
   - **`options.model` is a repo id string** (e.g. `"trymirai/Qwen3.5-0.8B-L"`) — the component does *not* download anything; `uzu` resolves and fetches the model itself the first time it runs.
   - **`huggingfaces` lists specific files/repos** — the component resolves and downloads them via the Hugging Face API/CDN itself, reporting progress through `event.onData` / `event.onResponse`, before starting the server.
3. `_server.start()` translates the `options` object into `cli server` flags (any `snake_case` key becomes a `--kebab-case` flag; strings, numbers, booleans, `File`/`Folder` values, and collections are all handled) and launches it as a `4D.SystemWorker`.
4. `event.onSuccess` fires once the server is up. Note: when the model was resolved as a plain repo id, the reported model list is a placeholder, since `uzu` — not the component — knows what it actually downloaded.

### Options object

Any key in the `options` object passed to `uzu.new()` is turned into a `cli server` command-line flag, for example:

```4d
$options:={model: "trymirai/Qwen3.5-0.8B-L"; port: 8080; max_tokens: 4096}
```

becomes:

```
cli server --model trymirai/Qwen3.5-0.8B-L --port 8080 --max-tokens 4096
```

`help` and `version` are handled specially and never emitted as generic flags. Unlike the local-model-path style of other engines, `uzu` does not accept a local model file path — it expects a Hugging Face repo id and manages its own local cache.

### Events

`cs.event.event` accepts formulas/functions for:

- `onError($params; $error)` — port conflict or other startup failure
- `onSuccess($params; $models)` — server is up and serving these models
- `onData($request; $event)` — Hugging Face download progress (only relevant when the component itself is downloading assets)
- `onResponse($request; $event)` — a download finished
- `onTerminate($worker; $params)` — the `cli` process exited

## Credits

- Native runtime: [trymirai/uzu](https://github.com/trymirai/uzu) — a high-performance local inference engine for AI models.
- This repository provides the 4D-side glue (process management, model resolution, event wiring) to run uzu as an embedded local LLM server inside a 4D application.
