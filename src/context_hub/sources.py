from __future__ import annotations
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import requests
from .io import write_json

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def download_preserve_last_good(source: dict, target: str | Path, status_path: str | Path, timeout: int = 60) -> dict:
    """Download atomically. A failed source never erases the last good snapshot."""
    target = Path(target); status_path = Path(status_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    previous = {}
    if status_path.exists():
        try:
            import json
            previous = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            previous = {}
    try:
        response = requests.get(source["source_url"], timeout=timeout, headers={"User-Agent":"ContextHubChile/0.1"})
        response.raise_for_status()
        data = response.content
        if not data:
            raise ValueError("empty response")
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_bytes(data); tmp.replace(target)
        status = {
            "source_id":source["source_id"],"status":"CURRENT",
            "last_successful_refresh_at":now,"last_attempt_at":now,
            "content_sha256":sha256_bytes(data),"bytes":len(data),"error":None,
        }
    except Exception as exc:
        status = {
            "source_id":source["source_id"],
            "status":"STALE" if target.exists() else "UNKNOWN",
            "last_successful_refresh_at":previous.get("last_successful_refresh_at"),
            "last_attempt_at":now,
            "content_sha256":previous.get("content_sha256"),
            "bytes":target.stat().st_size if target.exists() else 0,
            "error":f"{type(exc).__name__}: {exc}",
        }
    write_json(status_path, status)
    return status

def query_arcgis_features(source: dict, timeout: int = 60) -> tuple[list[dict], dict]:
    now = datetime.now(timezone.utc).isoformat()
    url = source["source_url"].rstrip("/") + "/query"
    params = {
        "where":"1=1",
        "outFields":"CUT_REG,CUT_PROV,CUT_COM,REGION,PROVINCIA,COMUNA",
        "returnGeometry":"false",
        "orderByFields":"CUT_COM",
        "f":"json",
    }
    response = requests.get(url, params=params, timeout=timeout, headers={"User-Agent":"ContextHubChile/0.1"})
    response.raise_for_status()
    payload=response.json()
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    features=payload.get("features") or []
    return features, {
        "source_id":source["source_id"],"status":"CURRENT","last_successful_refresh_at":now,
        "last_attempt_at":now,"feature_count":len(features),"error":None
    }
