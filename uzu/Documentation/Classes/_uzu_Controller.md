# _uzu_Controller
### Extends `_CLI_Controller` with uzu-specific worker termination handling.

> _uzu_Controller.new (CLI : cs.uzu._CLI)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| CLI | cs.uzu._CLI | -> | The owning `_CLI` (typically a `_server` instance) |

## Description

`_uzu_Controller` is the default controller used by all `_uzu` subclasses. It inherits all queueing and execution behaviour from [`_CLI_Controller`](_CLI_Controller.md) and overrides only `onTerminate` to forward the termination event back to the owning `_uzu` instance's `onTerminate` callback.

This allows application code to attach a single `onTerminate` function on the `_server` (or `uzu`) instance and have it called automatically when the `uzu-server` process exits.

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

To handle stdout while the server is running, create a subclass of `_uzu_Controller` and override `onData`:

```4d
// In your custom controller class (e.g. cs.uzu.MyController):
Class extends cs.uzu._uzu_Controller

Function onData($worker : 4D.SystemWorker; $params : Object)
    LOG EVENT(Into 4D debug message; $params.data)
```

Then pass it when constructing the server:

```4d
$uzu:=cs.uzu.uzu.new($port; $huggingfaces; $homeFolder; $options; $event)
// _uzu automatically detects MyController extends _uzu_Controller
// and uses it in place of the default
```

## See also

- [`_CLI_Controller`](_CLI_Controller.md) — parent class
- [`_uzu`](_uzu.md) — attaches this controller by default
- [`_server`](_server.md) — the `_uzu` subclass whose `onTerminate` is forwarded here
