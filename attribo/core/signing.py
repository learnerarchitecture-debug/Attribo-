"""
Tamper-evident report signing (offline, HMAC-SHA256).

The certificate embeds a short signature over (report ID, document hash,
scores, timestamp). Re-verify inside the app: the stored scan row is found by
report ID and the signature is recomputed and compared.

What it proves: the certificate/report pair was produced by this app from the
stored scan and was not edited afterwards outside the app.
What it does NOT prove: authorship, or that the document is honest.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import hashlib
import hmac

from ..licensing.keycheck import _SECRET

PREFIX = "SIG-"


def _digest(data: str) -> str:
    return hmac.new(_SECRET, data.encode("utf-8"), hashlib.sha256).hexdigest()[:16].upper()


def payload(report_id, doc_hash, similarity, integrity, ai, timestamp) -> str:
    return "|".join(
        [
            str(report_id or ""),
            str(doc_hash or "")[:32],
            f"{float(similarity or 0):.1f}",
            f"{float(integrity or 0):.1f}",
            f"{float(ai or 0):.1f}",
            str(timestamp or ""),
        ]
    )


def sign_fields(report_id, doc_hash, similarity, integrity, ai, timestamp) -> str:
    """Signature over explicit field values (works for stored rows too)."""
    return PREFIX + _digest(
        payload(report_id, doc_hash, similarity, integrity, ai, timestamp)
    )


def sign_result(result) -> str:
    return sign_fields(
        result.report_id,
        result.doc_hash,
        result.similarity,
        result.integrity,
        result.ai_likelihood,
        result.timestamp,
    )


def verify(report_id, doc_hash, similarity, integrity, ai, timestamp, signature) -> bool:
    data = payload(report_id, doc_hash, similarity, integrity, ai, timestamp)
    return hmac.compare_digest(PREFIX + _digest(data), str(signature or ""))
