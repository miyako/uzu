# _Model

Extends [`_models`](_models.md) to launch `cli server`.

> _Model.new (port : Integer; huggingfaces : cs.event.huggingfaces; options : Object; formula : 4D.Function; event : cs.event.event)

The constructor starts component-managed downloads only when the base class has
not delegated model resolution to Uzu (`offline` is false). Non-empty identifier
strings and existing local folders bypass that download queue.

## models () -> cs.event.models

For folder models, returns an entry using `options.model.name` and its existence
state. Text identifiers return an unnamed placeholder: the native process, not
the component, knows the resolved/downloaded model. Query `/v1/models` after
readiness for authoritative information.

## onDownload (oid : Text)

For legacy component-managed downloads, if `options.model` is not set, selects
the descriptor's **folder**, not the individual weights file, as the model
directory. Calls the base method to remove the completed entry and starts once
all files are available. The folder must contain a complete Uzu-compatible
model; arbitrary GGUF files are not supported.

## _onNothingToDownload ()

Called by `download()` when legacy descriptors resolved no files. Calls
`start()` only when `options.model` is an existing `4D.Folder`. Otherwise it
calls `event.onError` with code `2` (naming the folder path when one was given)
and does not launch. Identifier and existing-folder models never reach this
path: they are delegated to Uzu and launched by the `start` method.

## start ()

Launches at most once per instance; later calls are ignored (for example when
the same file OID completes twice). Refuses to launch when `options.model` is
neither non-empty text nor an existing `4D.File`/`4D.Folder` (for example when
the Hugging Face API was unreachable and the descriptor's local folder does not
exist): it calls `event.onError` with code `2`, naming the path when one was
given, instead of starting the server without `--model`. Otherwise creates `cs.workers.worker` for `_server`, calls `start(port; options)` and then
fires `event.onSuccess`. This is a **launch notification**, not a readiness
probe. It does not wait for model download or HTTP availability.

See [`uzu`](uzu.md) for public usage and [`_server`](_server.md) for arguments.
