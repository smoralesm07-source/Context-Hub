from pathlib import Path
import json
import context_hub.sources as s

def test_failed_download_preserves_last_good(tmp_path, monkeypatch):
    target=tmp_path/"source.bin"
    target.write_bytes(b"GOOD")
    status=tmp_path/"status.json"
    status.write_text(json.dumps({"last_successful_refresh_at":"2026-01-01","content_sha256":"abc"}))
    def boom(*a,**k): raise RuntimeError("offline")
    monkeypatch.setattr(s.requests,"get",boom)
    out=s.download_preserve_last_good({"source_id":"X","source_url":"https://invalid.test"},target,status)
    assert target.read_bytes()==b"GOOD"
    assert out["status"]=="STALE"
    assert out["last_successful_refresh_at"]=="2026-01-01"
