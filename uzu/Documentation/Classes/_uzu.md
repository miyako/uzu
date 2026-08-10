# _uzu
### Extends `_CLI` to target a specific uzu executable.

> _uzu.new (command : Text; class : 4D.Class)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| command | Text | -> | Logical command name; maps to an executable (see table below) |
| class | 4D.Class | -> | Optional custom controller class (must extend `_uzu_Controller`) |

## Description

`_uzu` extends [`_CLI`](_CLI.md) and resolves the `command` argument to the appropriate uzu binary name before passing it to the parent constructor. It also walks the inheritance chain of the supplied `class` to decide whether to use it as a custom controller or fall back to the default `_uzu_Controller`.

### Command mapping

| command value | Executable |
| --- | --- |
| `"embedding"` | `uzu-embedding` |
| `"gguf"` | `uzu-gguf` |
| `"quantize"` | `uzu-quantize` |
| `"cli"` | `uzu-cli` |
| `"tokenize"` | `uzu-tokenize` |
| _(any other value)_ | `uzu-server` |

### Properties

In addition to properties inherited from `_CLI`:

| Property | Type | Description |
| --- | --- | --- |
| port | Integer | Port the server is listening on |
| onData | 4D.Function | Forwarded to the controller's `onData` handler |
| onDataError | 4D.Function | Forwarded to the controller's `onDataError` handler |
| onTerminate | 4D.Function | Called by `_uzu_Controller` when the worker terminates |

### Methods

#### bind (option : Object; properties : Collection) → cs.uzu._CLI

Copies listed property names from `option` into `This`, used to bind event callbacks from an options object before execution.

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| option | Object | -> | Source object |
| properties | Collection | -> | Property names to copy |
| Result | cs.uzu._CLI | <- | `This` |

#### get worker () → 4D.SystemWorker

Returns the active `4D.SystemWorker` from the attached controller.

#### terminate ()

Delegates to `controller.terminate()`, stopping the active worker and draining the command queue.

## See also

- [`_CLI`](_CLI.md) — parent class
- [`_uzu_Controller`](_uzu_Controller.md) — default controller
- [`_server`](_server.md) — extends `_uzu` for `uzu-server`
