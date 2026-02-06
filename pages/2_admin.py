"""Painel administrativo da Rifa Amiga."""

from __future__ import annotations

import streamlit as st

from utils.components import format_number
from utils.raffle_service import (
    confirm_ticket,
    confirm_ticket_manual,
    confirm_tickets_bulk,
    create_raffle,
    draw_winner,
    get_active_raffle,
    get_tickets,
    get_tickets_by_status,
    get_winner_ticket,
    reject_ticket,
    reject_tickets_bulk,
    update_raffle,
)
from utils.styles import HIDE_STREAMLIT_CHROME
from utils.supabase_client import get_supabase

# ── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(page_title="Admin — Rifa Amiga", page_icon=":lock:", layout="wide")
st.markdown(HIDE_STREAMLIT_CHROME, unsafe_allow_html=True)

sb = get_supabase()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTENTICAÇÃO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _init_auth() -> bool:
    """Gerencia login. Retorna True se autenticado."""
    if "admin_session" not in st.session_state:
        st.session_state["admin_session"] = None

    if st.session_state["admin_session"] is not None:
        return True

    st.markdown("## :lock: Login do Administrador")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            try:
                resp = sb.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                st.session_state["admin_session"] = resp.session
                st.rerun()
            except Exception as e:
                st.error(f"Falha no login: {e}")
    return False


if not _init_auth():
    st.stop()


# ── Logado ───────────────────────────────────────────────────────────────────
st.markdown("## :shield: Painel Administrativo")

if st.sidebar.button("Sair"):
    st.session_state["admin_session"] = None
    st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ABAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
raffle = get_active_raffle()

tab_config, tab_reservas, tab_manual, tab_sorteio, tab_visao = st.tabs(
    ["Config", "Reservas", "Manual", "Sorteio", "Visão geral"]
)


# ── TAB: Configuração ────────────────────────────────────────────────────────
def _tab_config_create() -> None:
    """Formulário de criação de uma nova rifa."""
    st.info("Nenhuma rifa ativa. Crie uma abaixo.")
    with st.form("create_raffle"):
        title = st.text_input("Título da rifa", value="Rifa Solidária — Cadeira de Rodas")
        description = st.text_area("Descrição")
        total_numbers = st.number_input(
            "Quantidade de números", min_value=10, max_value=1000, value=100, step=10
        )
        price = st.number_input("Valor por número (R$)", min_value=0.5, value=10.0, step=0.5)
        pix_key = st.text_input("Chave PIX")
        pix_name = st.text_input("Nome do titular da chave PIX")

        if st.form_submit_button("Criar rifa", use_container_width=True):
            if not title.strip() or not pix_key.strip():
                st.error("Preencha título e chave PIX.")
            else:
                with st.spinner("Criando rifa..."):
                    create_raffle(
                        title=title.strip(),
                        description=description.strip(),
                        total_numbers=int(total_numbers),
                        price=float(price),
                        pix_key=pix_key.strip(),
                        pix_name=pix_name.strip(),
                    )
                st.success(f"Rifa criada com {int(total_numbers)} números!")
                st.rerun()


def _tab_config_edit(raffle: dict) -> None:
    """Formulário de edição da rifa ativa."""
    st.subheader(f"Rifa ativa: {raffle['title']}")
    with st.form("edit_raffle"):
        new_title = st.text_input("Título", value=raffle["title"])
        new_desc = st.text_area("Descrição", value=raffle.get("description", ""))
        new_price = st.number_input(
            "Valor por número (R$)",
            min_value=0.5,
            value=float(raffle["price"]),
            step=0.5,
        )
        new_pix = st.text_input("Chave PIX", value=raffle.get("pix_key", ""))
        new_pix_name = st.text_input(
            "Nome do titular da chave PIX", value=raffle.get("pix_name", "")
        )

        if st.form_submit_button("Salvar alterações", use_container_width=True):
            update_raffle(
                raffle["id"],
                title=new_title.strip(),
                description=new_desc.strip(),
                price=float(new_price),
                pix_key=new_pix.strip(),
                pix_name=new_pix_name.strip(),
            )
            st.success("Rifa atualizada!")
            st.rerun()


with tab_config:
    if raffle is None:
        _tab_config_create()
    else:
        _tab_config_edit(raffle)


# ── TAB: Reservas pendentes ──────────────────────────────────────────────────
def _render_ticket_expander(ticket: dict) -> None:
    """Renderiza um expander com detalhes e ações para um ticket reservado."""
    label = f"Número {format_number(ticket['number'])} — {ticket.get('buyer_name', 'Sem nome')}"
    with st.expander(label, expanded=False):
        st.write(f"**Nome:** {ticket.get('buyer_name', '-')}")
        st.write(f"**Reservado em:** {ticket.get('reserved_at', '-')}")

        proof = ticket.get("proof_url")
        if proof:
            st.image(proof, caption="Comprovante", use_container_width=True)
        else:
            st.warning("Sem comprovante anexado.")

        col_ok, col_no = st.columns(2)
        with col_ok:
            if st.button("Confirmar", key=f"confirm_{ticket['number']}", use_container_width=True):
                confirm_ticket(ticket["id"])
                st.success(f"Número {format_number(ticket['number'])} confirmado!")
                st.rerun()
        with col_no:
            if st.button(
                "Rejeitar", key=f"reject_{ticket['number']}",
                type="secondary", use_container_width=True,
            ):
                reject_ticket(ticket["id"])
                st.warning(f"Número {format_number(ticket['number'])} liberado.")
                st.rerun()


def _tab_reservas(raffle: dict) -> None:
    """Exibe e gerencia reservas pendentes."""
    reserved = get_tickets_by_status(raffle["id"], "reserved")

    if not reserved:
        st.info("Nenhuma reserva pendente.")
        return

    st.markdown(f"**{len(reserved)}** reserva(s) pendente(s)")

    col_all_ok, col_all_no = st.columns(2)
    with col_all_ok:
        if st.button("Confirmar todas", use_container_width=True, type="primary"):
            count = confirm_tickets_bulk(reserved)
            st.success(f"{count} reserva(s) confirmada(s)!")
            st.rerun()
    with col_all_no:
        if st.button("Rejeitar todas", use_container_width=True, type="secondary"):
            count = reject_tickets_bulk(reserved)
            st.warning(f"{count} reserva(s) rejeitada(s).")
            st.rerun()

    st.divider()
    for ticket in reserved:
        _render_ticket_expander(ticket)


with tab_reservas:
    if raffle is None:
        st.warning("Crie uma rifa primeiro.")
    else:
        _tab_reservas(raffle)


# ── TAB: Confirmar manual ────────────────────────────────────────────────────
def _tab_manual(raffle: dict) -> None:
    """Confirmação manual para pagamentos presenciais."""
    st.markdown(
        "Use esta aba para confirmar números de quem pagou presencialmente, "
        "sem precisar de comprovante."
    )
    available = get_tickets_by_status(raffle["id"], "available")

    if not available:
        st.info("Nenhum número disponível.")
        return

    with st.form("manual_confirm"):
        options = [format_number(t["number"]) for t in available]
        selected = st.selectbox("Número", options)
        buyer = st.text_input("Nome do comprador")

        if st.form_submit_button("Confirmar número", use_container_width=True):
            if not buyer.strip():
                st.error("Preencha o nome do comprador.")
            else:
                num = int(selected)
                confirm_ticket_manual(raffle["id"], num, buyer.strip())
                st.success(f"Número {format_number(num)} confirmado para {buyer.strip()}!")
                st.rerun()


with tab_manual:
    if raffle is None:
        st.warning("Crie uma rifa primeiro.")
    else:
        _tab_manual(raffle)


# ── TAB: Sorteio ─────────────────────────────────────────────────────────────
def _tab_sorteio_finished(raffle: dict) -> None:
    """Exibe resultado quando o sorteio já foi realizado."""
    st.balloons()
    winner = get_winner_ticket(raffle["id"], raffle["winner_number"])
    winner_name = winner.get("buyer_name", "-") if winner else "-"
    st.success(
        f"Número sorteado: **{format_number(raffle['winner_number'])}** — "
        f"Ganhador(a): **{winner_name}**"
    )


def _tab_sorteio_pending(raffle: dict) -> None:
    """Botão de sorteio quando há números confirmados."""
    confirmed = get_tickets_by_status(raffle["id"], "confirmed", "number, buyer_name")

    if not confirmed:
        st.warning("Nenhum número confirmado ainda. Confirme pagamentos primeiro.")
        return

    st.info(f"**{len(confirmed)}** número(s) confirmado(s) participando do sorteio.")
    st.markdown("---")

    if st.button("SORTEAR", use_container_width=True, type="primary"):
        winner = draw_winner(raffle["id"])
        st.balloons()
        st.success(
            f"Número sorteado: **{format_number(winner['number'])}** — "
            f"Ganhador(a): **{winner.get('buyer_name', '-')}**"
        )
        st.rerun()


with tab_sorteio:
    if raffle is None:
        st.warning("Crie uma rifa primeiro.")
    elif raffle.get("winner_number") is not None:
        _tab_sorteio_finished(raffle)
    else:
        _tab_sorteio_pending(raffle)


# ── TAB: Visão geral ─────────────────────────────────────────────────────────
def _tab_visao(raffle: dict) -> None:
    """Dashboard com métricas e tabela de vendas."""
    all_tickets = get_tickets(raffle["id"])
    total = len(all_tickets)
    price = float(raffle["price"])

    counts = {"available": 0, "reserved": 0, "confirmed": 0}
    for t in all_tickets:
        status = t["status"]
        if status in counts:
            counts[status] += 1

    c1, c2 = st.columns(2)
    c1.metric("Total", total)
    c2.metric("Disponíveis", counts["available"])
    c3, c4 = st.columns(2)
    c3.metric("Reservados", counts["reserved"])
    c4.metric("Confirmados", counts["confirmed"])

    revenue = counts["confirmed"] * price
    st.metric("Valor arrecadado (confirmados)", f"R$ {revenue:.2f}")
    progress = counts["confirmed"] / total if total > 0 else 0
    st.progress(progress, text=f"{counts['confirmed']}/{total} confirmados")

    st.divider()
    _render_sales_table(all_tickets)


def _render_sales_table(all_tickets: list[dict]) -> None:
    """Exibe tabela de tickets vendidos/reservados."""
    sold = [t for t in all_tickets if t["status"] != "available"]
    if not sold:
        st.info("Nenhum número vendido ainda.")
        return

    import pandas as pd

    columns = ["number", "status", "buyer_name", "reserved_at", "confirmed_at"]
    labels = ["Número", "Status", "Nome", "Reservado em", "Confirmado em"]
    df = pd.DataFrame(sold)[columns]
    df.columns = labels
    st.dataframe(df, use_container_width=True, hide_index=True)


with tab_visao:
    if raffle is None:
        st.warning("Crie uma rifa primeiro.")
    else:
        _tab_visao(raffle)
