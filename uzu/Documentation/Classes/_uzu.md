# _uzu

Extends [`_CLI`](_CLI.md) for Uzu's **`cli`** executable.

> _uzu.new (class : 4D.Class)

The optional class must extend `_uzu_Controller`; the constructor walks the
inheritance chain to select it or uses the default controller. There is no
llama.cpp-style executable command mapping. `_server` adds the `server`
subcommand when building the invocation.

| Property | Type | Description |
| --- | --- | --- |
| port | Integer | Managed listening port |
| onData | 4D.Function | stdout callback property |
| onDataError | 4D.Function | stderr callback property |
| onTerminate | 4D.Function | Forwarded by `_uzu_Controller` on process exit |

## bind (option : Object; properties : Collection) -> cs.uzu._CLI

Copies the listed option properties onto the instance; returns `This`.

## worker -> 4D.SystemWorker

Returns the attached controller's active worker.

## terminate ()

Delegates to `controller.terminate()`, stopping the worker and draining its queue.

See [`_uzu_Controller`](_uzu_Controller.md) and [`_server`](_server.md).
