# Civitai Model Organizer

Desktop tool for sorting local Civitai model files by their model-version SHA-256 hash. Supports Checkpoint, TextualInversion, LORA, VAE and LoCon.

## Quick start

Install Python 3.10+ with Tkinter:

```sh
python -m pip install -r requirements.txt
python civitai_modules_orgnizer_v1.py
```

Choose a folder, preview changes with **Dry run** (enabled by default), then uncheck it and confirm to move files. Files with unrecognized metadata remain untouched. The tool searches the *top level* of the folder, not subfolders.

## Safety improvements

- UI updates are sent through a thread-safe queue; requests/hashing run in the worker.
- Cache is keyed by content SHA-256, never basename, so overwritten files cannot inherit stale classifications.
- Requests have a 15-second timeout; unknown/unavailable API responses leave files untouched.
- Colliding destination names receive numeric suffixes; files are never overwritten.
- No folders are created during preview.
- SHA hashing is streamed in 1 MiB blocks.
- Successful cache entries are stored in `.module_organizer_cache.json` using atomic replacement.

Network access is needed for previously unseen hashes. Check classifications in the preview: model-type labels depend on the service's current metadata.

## Tests

```sh
python -m unittest discover -s tests -v
```
