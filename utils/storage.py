from __future__ import annotations

import time
from io import BytesIO

import streamlit as st

from utils.supabase_client import get_supabase

BUCKET = "proofs"


def upload_proof(raffle_id: str, ticket_number: int, file) -> str:
    """Faz upload do comprovante e retorna a URL publica."""
    sb = get_supabase()
    timestamp = int(time.time())
    ext = file.name.rsplit(".", 1)[-1] if "." in file.name else "png"
    path = f"{raffle_id}/{ticket_number}_{timestamp}.{ext}"

    file_bytes = file.read()

    sb.storage.from_(BUCKET).upload(
        path,
        file_bytes,
        file_options={"content-type": file.type or "image/png"},
    )

    url = sb.storage.from_(BUCKET).get_public_url(path)
    return url


def get_proof_url(proof_url: str | None) -> str | None:
    """Retorna a URL do comprovante (ja e publica)."""
    return proof_url
