"""Safe, testable sorting core for local model files."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable

EXTENSIONS={".pt",".bin",".ckpt",".safetensors",".pickle",".pkl"}
CATEGORIES={"Checkpoint","TextualInversion","LORA","VAE","LoCon"}
API_URL="https://civitai.com/api/v1/model-versions/by-hash/"
MAX_MODEL_BYTES=128*1024*1024*1024


def sha256_file(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_model_type(sha256: str, *, session=None, timeout=15):
    import requests
    client=session or requests
    try:
        response=client.get(API_URL+sha256, timeout=timeout)
        if response.status_code==404:
            return None
        response.raise_for_status()
        model=response.json().get("model") or {}
        category=model.get("type")
        return category if category in CATEGORIES else None
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        return None


def load_cache(path: Path) -> dict:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):
        return {}


def save_cache(path: Path,cache: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix=".module_cache_",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            json.dump(cache,handle,indent=2,sort_keys=True)
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def unique_destination(folder: Path, filename: str) -> Path:
    base=folder/filename
    if not base.exists():
        return base
    stem,suffix=Path(filename).stem,Path(filename).suffix
    i=1
    while True:
        candidate=folder/f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i+=1


def organize(folder: Path, *, dry_run=True, on_progress: Callable=lambda event:None,
             resolver=detect_model_type) -> dict:
    """Only move when the hash is resolved to a recognized category.

    No recursion, no overwrites. Cache keys are hashes (not stale filenames).
    """
    folder=Path(folder).expanduser().resolve()
    if not folder.is_dir():
        raise ValueError("Select an existing directory.")
    cache_path=folder/".module_organizer_cache.json"
    cache=load_cache(cache_path)
    files=sorted((p for p in folder.iterdir() if p.is_file()
                  and p.suffix.lower() in EXTENSIONS),key=lambda p:p.name.lower())
    stats={"found":len(files),"moved":0,"planned":0,"unresolved":0,"errors":0}
    for i,p in enumerate(files,1):
        try:
            # avoid mistakenly moving abnormally huge/special files
            if p.stat().st_size>MAX_MODEL_BYTES or p.is_symlink():
                raise ValueError("Refusing symlink or oversized model.")
            digest=sha256_file(p)
            category=cache.get(digest)
            if category not in CATEGORIES:
                category=resolver(digest)
                if category in CATEGORIES:
                    cache[digest]=category
            if category not in CATEGORIES:
                stats["unresolved"]+=1
                on_progress((i,len(files),p.name,"Unknown type: left in place"))
                continue
            destination=unique_destination(folder/category,p.name)
            if dry_run:
                stats["planned"]+=1
                on_progress((i,len(files),p.name,f"Would move -> {category}/{destination.name}"))
            else:
                destination.parent.mkdir(exist_ok=True)
                shutil.move(str(p),str(destination))
                stats["moved"]+=1
                on_progress((i,len(files),p.name,f"Moved -> {category}/{destination.name}"))
        except (OSError,ValueError) as exc:
            stats["errors"]+=1
            on_progress((i,len(files),p.name,f"Error: {exc}"))
    if not dry_run and cache:
        save_cache(cache_path,cache)
    return stats
