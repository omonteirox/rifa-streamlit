"""Camada de serviço para operações com rifas e tickets no Supabase.

Centraliza todas as queries e mutações do banco, mantendo as páginas
Streamlit focadas apenas em apresentação e interação.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from utils.supabase_client import get_supabase

# ── Tipos auxiliares ─────────────────────────────────────────────────────────
type RaffleDict = dict[str, Any]
type TicketDict = dict[str, Any]

TICKET_BATCH_SIZE = 500


def _now_iso() -> str:
    """Retorna o timestamp UTC atual em formato ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


# ── Rifas ────────────────────────────────────────────────────────────────────

def get_active_raffle() -> RaffleDict | None:
    """Retorna a rifa ativa ou None."""
    sb = get_supabase()
    res = sb.table("raffles").select("*").eq("status", "active").limit(1).execute()
    return res.data[0] if res.data else None


def create_raffle(
    title: str,
    description: str,
    total_numbers: int,
    price: float,
    pix_key: str,
    pix_name: str,
) -> RaffleDict:
    """Cria uma rifa e gera todos os tickets em lote."""
    sb = get_supabase()

    new_raffle = (
        sb.table("raffles")
        .insert(
            {
                "title": title,
                "description": description,
                "total_numbers": total_numbers,
                "price": price,
                "pix_key": pix_key,
                "pix_name": pix_name,
                "status": "active",
            }
        )
        .execute()
    )
    raffle = new_raffle.data[0]
    _generate_tickets(raffle["id"], total_numbers)
    return raffle


def update_raffle(raffle_id: str, **fields: Any) -> None:
    """Atualiza campos arbitrários de uma rifa."""
    sb = get_supabase()
    sb.table("raffles").update(fields).eq("id", raffle_id).execute()


def set_winner(raffle_id: str, winner_number: int) -> None:
    """Registra o número vencedor e encerra a rifa."""
    update_raffle(raffle_id, winner_number=winner_number, status="finished")


# ── Tickets ──────────────────────────────────────────────────────────────────

def get_tickets(raffle_id: str, columns: str = "*") -> list[TicketDict]:
    """Retorna tickets de uma rifa ordenados por número."""
    sb = get_supabase()
    res = (
        sb.table("tickets")
        .select(columns)
        .eq("raffle_id", raffle_id)
        .order("number")
        .execute()
    )
    return res.data


def get_tickets_by_status(
    raffle_id: str, status: str, columns: str = "*"
) -> list[TicketDict]:
    """Retorna tickets filtrados por status."""
    sb = get_supabase()
    res = (
        sb.table("tickets")
        .select(columns)
        .eq("raffle_id", raffle_id)
        .eq("status", status)
        .order("number")
        .execute()
    )
    return res.data


def reserve_tickets(
    raffle_id: str,
    numbers: list[int],
    buyer_name: str,
    proof_url: str,
) -> None:
    """Reserva uma lista de números para um comprador."""
    sb = get_supabase()
    now = _now_iso()
    for number in numbers:
        sb.table("tickets").update(
            {
                "status": "reserved",
                "buyer_name": buyer_name,
                "proof_url": proof_url,
                "reserved_at": now,
            }
        ).eq("raffle_id", raffle_id).eq("number", number).eq(
            "status", "available"
        ).execute()


def confirm_ticket(ticket_id: str) -> None:
    """Confirma o pagamento de um ticket individual."""
    sb = get_supabase()
    sb.table("tickets").update(
        {"status": "confirmed", "confirmed_at": _now_iso()}
    ).eq("id", ticket_id).execute()


def confirm_tickets_bulk(tickets: list[TicketDict]) -> int:
    """Confirma o pagamento de vários tickets. Retorna a quantidade."""
    for ticket in tickets:
        confirm_ticket(ticket["id"])
    return len(tickets)


def reject_ticket(ticket_id: str) -> None:
    """Rejeita/libera um ticket, voltando ao estado disponível."""
    sb = get_supabase()
    sb.table("tickets").update(
        {
            "status": "available",
            "buyer_name": None,
            "proof_url": None,
            "reserved_at": None,
        }
    ).eq("id", ticket_id).execute()


def reject_tickets_bulk(tickets: list[TicketDict]) -> int:
    """Rejeita vários tickets. Retorna a quantidade."""
    for ticket in tickets:
        reject_ticket(ticket["id"])
    return len(tickets)


def confirm_ticket_manual(
    raffle_id: str, number: int, buyer_name: str
) -> None:
    """Confirma um número diretamente (pagamento presencial)."""
    sb = get_supabase()
    sb.table("tickets").update(
        {
            "status": "confirmed",
            "buyer_name": buyer_name,
            "confirmed_at": _now_iso(),
        }
    ).eq("raffle_id", raffle_id).eq("number", number).execute()


def get_winner_ticket(raffle_id: str, winner_number: int) -> TicketDict | None:
    """Retorna o ticket vencedor."""
    sb = get_supabase()
    res = (
        sb.table("tickets")
        .select("*")
        .eq("raffle_id", raffle_id)
        .eq("number", winner_number)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def draw_winner(raffle_id: str) -> TicketDict:
    """Sorteia um número entre os confirmados e registra o vencedor."""
    confirmed = get_tickets_by_status(raffle_id, "confirmed", "number, buyer_name")
    if not confirmed:
        raise ValueError("Nenhum número confirmado para sortear.")
    winner = random.choice(confirmed)
    set_winner(raffle_id, winner["number"])
    return winner


# ── Helpers internos ─────────────────────────────────────────────────────────

def _generate_tickets(raffle_id: str, total: int) -> None:
    """Gera os tickets da rifa em lotes."""
    sb = get_supabase()
    tickets = [
        {"raffle_id": raffle_id, "number": i, "status": "available"}
        for i in range(1, total + 1)
    ]
    for start in range(0, len(tickets), TICKET_BATCH_SIZE):
        chunk = tickets[start : start + TICKET_BATCH_SIZE]
        sb.table("tickets").insert(chunk).execute()
