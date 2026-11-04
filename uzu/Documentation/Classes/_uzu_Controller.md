# _uzu_Controller
### Extends `_CLI_Controller` with uzu-specific worker termination handling.

> _uzu_Controller.new (CLI : cs.uzu._CLI)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| CLI | cs.uzu._CLI | -> | The owning `_CLI` (typically a `_server` instance) |

## Description

`_uzu_Controller` is the default controller used by all `_uzu` subclasses. It inherits all queueing and execution behaviour from [`_CLI_Controller`](_CLI_Controller.md) and overrides only `onTerminate` to forward the termination event back to the owning `_uzu` instance's `onTerminate` callback.

This allows application code to attach a single `onTerminate` function on the `_server` instance and have it called automatically when the `cli server` process exits.

### Overridden event callbacks

The following callbacks are declared (but intentionally left as no-ops) and may be overridden in a subclass:

| Property | Description |
| --- | --- |
| onData | stdout data event |
| onDataError | stderr data event |
| onResponse | response / command-complete event |
| onError | worker error event |

#### onTerminate ($worker : 4D.SystemWorker; $params : Object)

Called when the managed `SystemWorker` terminates. Looks up `onTerminate` on the owning `_server` instance and calls it if present.

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| $worker | 4D.SystemWorker | -> | The worker that terminated |
| $params | Object | -> | Termination parameters from the system worker |

## Examples

### Custom controller subclass

stdout/stderr are quiet by default on purpose: a long-running server can produce a large amount of output. If you do handle streams, keep the handler bounded (do not accumulate the data). A subclass of `_uzu_Controller` can override `onData`:

```4d
// In your custom controller class (e.g. cs.uzu.MyController):
Class extends cs.uzu._uzu_Controller

Function onData($worker : 4D.SystemWorker; $params : Object)
    LOG EVENT(Into 4D debug message; $params.data)
```

`cs.uzu.uzu.new()` does not accept a controller and always uses the default `_uzu_Controller`. A custom controller is used only when you pass its class to `_server` yourself; `_uzu` accepts it when it extends `_uzu_Controller`:

```4d
var $server : cs.uzu._server
$server:=cs.uzu._server.new(cs.MyController)
$server.start($options)  // $options must already contain model, port, etc.
```

This bypasses the facade's port check and legacy Hugging Face downloads.

## See also

- [`_CLI_Controller`](_CLI_Controller.md) — parent class
- [`_uzu`](_uzu.md) — attaches this controller by default
- [`_server`](_server.md) — the `_uzu` subclass whose `onTerminate` is forwarded here
