# Civitai Model Organizer

A cautious desktop and command-line sorter for model files recognized by Civitai's model-version SHA-256 endpoint.

## Features

- Works with Checkpoint, TextualInversion, LORA, VAE and LoCon.
- Previews every move before touching files (the default).
- Hashes local model bytes, not just filenames; cached classifications cannot be reused for different content.
- Handles destination name collisions without overwriting.
- Optional **Scan subfolders**, preserving paths under the category folder and skipping already-sorted folders.
- Optional **Offline mode**, which looks up known hashes only in the local cache.
- CLI with structured JSON report for use in scripts, dashboards or scheduled batch jobs.
- Tk GUI remains responsive during hashing/network lookup.

## Install

Python 3.10+ with Tkinter and requests:

```sh
python -m pip install -r requirements.txt
python civitai_modules_orgnizer_v1.py
```

## Headless CLI

Preview without moving:

```sh
python organize_models.py "/path/to/models" --recursive
```

Preview without HTTP:

```sh
python organize_models.py "/path/to/models" --recursive --offline --json
```

Move recognized files (requires **both** flags):

```sh
python organize_models.py "/path/to/models" --recursive --apply --yes
```

**Important:** Recursive mode moves `models/subfolder/name.safetensors` into
`LORA/models/subfolder/name.safetensors` under the selected root. The old source tree is otherwise preserved; empty directories are not removed. Existing category folders are skipped in recursive scans.

A previously unseen hash in offline mode is reported as unresolved; the file remains untouched. Preview does not populate the persistent cache. The API may fail or return unsupported categories, in which case files remain in place.

For safety, do a dry run and review the summary before applying to real model libraries. Keeping a backup is recommended.

## Testing

```sh
python -m unittest discover -s tests -v
```

No network access is required by the tests. CI checks Python 3.10, 3.12 and 3.13.
