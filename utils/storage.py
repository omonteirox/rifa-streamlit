"""Upload de comprovantes de pagamento para o Supabase Storage."""

from __future__ import annotations

import time

from utils.supabase_client import get_supabase

_BUCKET = "proofs"
_DEFAULT_EXT = "png"
_DEFAULT_CONTENT_TYPE = "image/png"


def _build_storage_path(raffle_id: str, ticket_number: int, filename: str) -> str:
    """Monta o caminho de armazenamento do arquivo."""
    timestamp = int(time.time())
    ext = filename.rsplit(".", 1)[-1] if "." in filename else _DEFAULT_EXT
    return f"{raffle_id}/{ticket_number}_{timestamp}.{ext}"


def upload_proof(raffle_id: str, ticket_number: int, file) -> str:
    """Faz upload do comprovante e retorna a URL pública."""
    sb = get_supabase()
    path = _build_storage_path(raffle_id, ticket_number, file.name)

    sb.storage.from_(_BUCKET).upload(
        path,
        file.read(),
        file_options={"content-type": file.type or _DEFAULT_CONTENT_TYPE},
    )

    return sb.storage.from_(_BUCKET).get_public_url(path)
