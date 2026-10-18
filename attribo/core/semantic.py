"""
Optional semantic matching layer (ONNX sentence embeddings).

Downloads a small sentence-embedding model (~90 MB, all-MiniLM-L6-v2) on
first use. All embedding runs locally on CPU; document text never leaves
the machine. Everything degrades gracefully if the dependencies or model
files are missing.

(c) 2026 Attribo. All rights reserved.
"""
import json
import threading
from pathlib import Path

from ..storage.settings import APP_DIR

MODEL_DIR = APP_DIR / "models" / "minilm"
MODEL_FILE = MODEL_DIR / "model.onnx"
TOKENIZER_FILE = MODEL_DIR / "tokenizer.json"
META_FILE = MODEL_DIR / "meta.json"

HF_BASE = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main"
FILES = (
    ("onnx/model.onnx", MODEL_FILE),
    ("tokenizer.json", TOKENIZER_FILE),
)

MAX_LENGTH = 256

_lock = threading.Lock()
_session = None
_tokenizer = None


def deps_available() -> tuple:
    try:
        import numpy  # noqa: F401
        import onnxruntime  # noqa: F401
        import tokenizers  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return False, f"Semantic dependencies missing ({exc.__class__.__name__})."
    return True, ""


def model_available() -> tuple:
    ok, reason = deps_available()
    if not ok:
        return False, reason
    if not MODEL_FILE.exists() or not TOKENIZER_FILE.exists():
        return False, "Semantic model not downloaded yet."
    return True, ""


def status_text() -> str:
    ok, reason = model_available()
    if ok:
        size_mb = MODEL_FILE.stat().st_size / (1024 * 1024)
        return f"Semantic model ready ({size_mb:.0f} MB)."
    return reason


def download(progress=None) -> tuple:
    """Download the model files. progress(fraction, message) is optional."""
    import requests

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for remote, target in FILES:
        url = f"{HF_BASE}/{remote}"
        if target.exists() and target.stat().st_size > 0:
            continue
        try:
            with requests.get(url, stream=True, timeout=60) as response:
                if response.status_code != 200:
                    return False, f"Download failed (HTTP {response.status_code}) for {remote}."
                total = int(response.headers.get("content-length") or 0)
                done = 0
                tmp = target.with_name(target.name + ".part")
                with open(tmp, "wb") as fh:
                    for chunk in response.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
                        done += len(chunk)
                        if progress and total:
                            progress(min(1.0, done / total), f"Downloading {target.name}...")
                tmp.replace(target)
        except Exception as exc:  # noqa: BLE001
            return False, f"Download failed: {exc}"
    META_FILE.write_text(
        json.dumps({"model": "all-MiniLM-L6-v2", "format": "onnx"}), encoding="utf-8"
    )
    return True, "Semantic model downloaded."


def _load():
    global _session, _tokenizer
    with _lock:
        if _session is None:
            import onnxruntime as ort
            from tokenizers import Tokenizer

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 2
            opts.log_severity_level = 3
            _session = ort.InferenceSession(
                str(MODEL_FILE), sess_options=opts, providers=["CPUExecutionProvider"]
            )
            _tokenizer = Tokenizer.from_file(str(TOKENIZER_FILE))
            _tokenizer.enable_truncation(max_length=MAX_LENGTH)
    return _session, _tokenizer


def embed(texts: list, batch_size: int = 32):
    """Returns L2-normalized embeddings as a numpy float32 array (n, 384)."""
    import numpy as np

    session, tokenizer = _load()
    vectors = []
    for i in range(0, len(texts), batch_size):
        chunk = [t if str(t).strip() else " " for t in texts[i : i + batch_size]]
        encodings = tokenizer.encode_batch(chunk)
        ids = np.array([e.ids for e in encodings], dtype=np.int64)
        mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        types = np.zeros_like(ids)
        outputs = session.run(
            None, {"input_ids": ids, "attention_mask": mask, "token_type_ids": types}
        )
        token_embeddings = outputs[0]
        mask_f = mask[..., None].astype(np.float32)
        summed = (token_embeddings * mask_f).sum(axis=1)
        counts = np.clip(mask_f.sum(axis=1), 1e-9, None)
        mean = summed / counts
        norms = np.linalg.norm(mean, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vectors.append((mean / norms).astype(np.float32))
    if not vectors:
        return np.zeros((0, 384), dtype=np.float32)
    return np.vstack(vectors)
