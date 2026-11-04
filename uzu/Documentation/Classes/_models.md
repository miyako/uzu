# _models
### Abstract base class that resolves Hugging Face model metadata and manages file downloads.

> _models.new (port : Integer; huggingfaces : cs.event.huggingfaces; options : Object; formula : 4D.Function; event : cs.event.event)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| port | Integer | -> | Port stored in `options.port` |
| huggingfaces | cs.event.huggingfaces | -> | One or more Hugging Face model descriptors |
| options | Object | -> | Server options object (mutated to add `port`; when `event` is not `Null`, also `onTerminate`, `onStdErr`, `onStdOut`) |
| formula | 4D.Function | -> | Internal response callback forwarded to the download helper |
| event | cs.event.event | -> | Callback functions, or `Null` for no callbacks |

## Description

`_models` is the download-and-startup orchestrator. A non-empty text `options.model` (catalog ID, repository ID or native directory path) or an existing `4D.Folder` delegates model resolution to the native CLI immediately. The legacy `offline` property means the component skips its own download queue; it does **not** guarantee network-free native startup.

Otherwise it iterates `huggingfaces`, queries the Hugging Face API for file metadata (OID, size, path), and builds a `files` queue. Descriptors that resolve no file are recorded with the reason (unrecognized URL, HTTP status, named file not in the repository, no file matching `paths`, or a `folder` that is neither a `4D.Folder` nor a `4D.File`); [`_Model`](_Model.md) includes those reasons in the `onError` message when nothing is left to download. If the API is unreachable it attempts the descriptor's local folder; if that folder does not exist, [`_Model`](_Model.md)`.start()` reports `onError` code `2` rather than launching without a model. Descriptors must provide a complete Uzu-compatible directory, not a GGUF file; native resolution is recommended.

URL formats accepted in `huggingface.URL`:

| Format | Example |
| --- | --- |
| Full HTTPS URL | `https://huggingface.co/user/repo` |
| Short `user/repo` path | A supported Uzu model repository |

### Properties

| Property | Type | Description |
| --- | --- | --- |
| huggingfaces | cs.event.huggingfaces | Original descriptor collection |
| files | Collection | Resolved file metadata objects pending download |
| options | Object | Merged server options |
| event | cs.event.event | Callback functions |
| offline | Boolean | Skip component downloads: native identifier/folder supplied, or API unreachable |

### Methods

#### download ()

If `files` is empty (nothing to download), calls `_onNothingToDownload()` instead and returns. Otherwise iterates `files`. For each file that is already present on disk with the correct size, `onDownload` is called immediately (skipping the HTTP fetch). Otherwise a `cs.event.download` is created to fetch the file from Hugging Face.

#### onDownload (oid : Text)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| oid | Text | -> | OID of the file that finished downloading |

Removes the completed file from `files`. When `files` is empty (all downloads done) it calls `start()`.

#### _onNothingToDownload () *(virtual)*

Called by `download()` when there are no files to download. The base implementation calls `start()`. Overridden in [`_Model`](_Model.md).

#### _notifyError (error : cs.event.error)

Calls `event.onError` with receiver `This` and arguments `(options; error)` when `event` is not `Null` and `onError` is a function; otherwise does nothing.

#### models () → cs.event.models *(virtual)*

Returns a `cs.event.models` instance describing the loaded models. The base implementation returns an empty collection. Overridden in [`_Model`](_Model.md).

#### start () *(virtual)*

Called automatically when all downloads complete (or by `_onNothingToDownload()`). The base implementation is a no-op. Overridden in [`_Model`](_Model.md) to launch the server.

## See also

- [`_Model`](_Model.md) — concrete subclass that overrides `models()`, `onDownload()`, `_onNothingToDownload()` and `start()`
- [`uzu`](uzu.md) — the public entry point
