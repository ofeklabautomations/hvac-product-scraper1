import hashlib
import os
import re
from urllib.parse import urlparse, urljoin

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def safe_filename(name: str) -> str:
    return SAFE_NAME_RE.sub("_", name)[:160]

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def join_url(base: str, href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return urljoin(base, href)

