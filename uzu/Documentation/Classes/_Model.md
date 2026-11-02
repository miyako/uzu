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

## start ()

Creates `cs.workers.worker` for `_server`, calls `start(port; options)` and then
fires `event.onSuccess`. This is a **launch notification**, not a readiness
probe. It does not wait for model download or HTTP availability.

See [`uzu`](uzu.md) for public usage and [`_server`](_server.md) for arguments.
