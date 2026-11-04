# _server

Extends [`_uzu`](_uzu.md) to launch **`cli server`**.

> _server.new (controller : 4D.Class)

The optional controller class extends `_uzu_Controller`. Application code
normally uses [`cs.uzu.uzu`](uzu.md); the workers component manages `_server`.

## start (option : Object) -> 4D.SystemWorker

Binds `onTerminate`, escapes the executable path, appends the `server`
subcommand, and converts option entries into arguments before passing the command
to `_CLI_Controller.execute`.

| Value | Command form |
| --- | --- |
| Number | `--flag value` (always `.` as decimal separator, regardless of system locale) |
| Text | `--flag escaped-value` |
| Boolean true | `--flag` |
| Existing 4D.File / 4D.Folder | `--flag escaped-path` |
| Collection | Flag repeated for each supported element |

Keys use kebab case (`no_prefix_cache` -> `--no-prefix-cache`). `help`, `version`
and event callback keys are excluded. Generic argument conversion does **not**
imply that every option is supported: the current server's flags are documented
in [`uzu`](uzu.md). In particular, `model` must be a supported identifier or a
complete compatible directory, not an individual model file.

The wrapper does not create per-launch cache directories. Native Uzu manages
its own persistent storage; `HF_HUB_CACHE`/`LLAMA_CACHE` overrides are not used.

```4d
$uzu:=cs.uzu.uzu.new(8080; Null; $homeFolder; \
    {model: "alibaba:qwen3.5:0.8b:mirai:mirai-m:4"}; $event)
```

See [`_CLI`](_CLI.md) for executable resolution and escaping, and
[`_CLI_Controller`](_CLI_Controller.md) for execution/lifecycle details.
