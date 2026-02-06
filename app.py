"""Página principal da Rifa Amiga — exibição pública."""

import streamlit as st

from utils.components import (
    format_number,
    format_numbers_list,
    render_footer,
    render_legend,
    render_number_grid,
    render_pix_box,
)
from utils.raffle_service import get_active_raffle, get_tickets, reserve_tickets
from utils.storage import upload_proof
from utils.styles import MAIN_PAGE_CSS

# ── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Rifa Amiga",
    page_icon=":wheelchair:",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(MAIN_PAGE_CSS, unsafe_allow_html=True)


# ── Dados com cache ──────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def _load_raffle():
    return get_active_raffle()


@st.cache_data(ttl=5)
def _load_tickets(raffle_id: str):
    return get_tickets(raffle_id, columns="number, status, buyer_name")


# ── Seções da página ─────────────────────────────────────────────────────────
def _show_raffle_header(raffle: dict) -> None:
    """Exibe título, descrição e dados PIX da rifa."""
    st.markdown(f"### {raffle['title']}")
    if raffle.get("description"):
        st.markdown(raffle["description"])

    st.metric("Valor por número", f"R$ {float(raffle['price']):.2f}")
    render_pix_box(
        raffle.get("pix_name", ""),
        raffle.get("pix_key", ""),
    )


def _show_winner_banner(raffle: dict) -> None:
    """Exibe banner de vencedor, se houver."""
    if raffle.get("winner_number") is not None:
        st.balloons()
        st.success(
            f"Rifa encerrada! Número sorteado: "
            f"**{format_number(raffle['winner_number'])}**"
        )


def _show_reservation_form(raffle: dict, available_numbers: list[int]) -> None:
    """Formulário para o comprador reservar números."""
    st.divider()
    st.subheader("Escolha seu(s) número(s)")

    options = [format_number(n) for n in available_numbers]
    selected = st.multiselect(
        "Selecione um ou mais números disponíveis",
        options,
        placeholder="Clique para escolher...",
    )
    if not selected:
        return

    selected_nums = [int(s) for s in selected]
    total = len(selected_nums) * float(raffle["price"])
    st.info(
        f"**{len(selected_nums)}** número(s) selecionado(s) — "
        f"Total: **R$ {total:.2f}**"
    )

    with st.form("reserve_form"):
        buyer_name = st.text_input("Seu nome completo")
        buyer_phone = st.text_input(
            "Telefone com DDD", placeholder="(62) 99999-9999"
        )
        proof_file = st.file_uploader(
            "Comprovante de pagamento (imagem)",
            type=["png", "jpg", "jpeg", "webp"],
        )
        submitted = st.form_submit_button(
            "Enviar e reservar", use_container_width=True
        )

        if submitted:
            _handle_reservation(
                raffle, selected_nums, buyer_name, buyer_phone, proof_file
            )


def _handle_reservation(
    raffle: dict,
    selected_nums: list[int],
    buyer_name: str,
    buyer_phone: str,
    proof_file,
) -> None:
    """Valida e processa a reserva de números."""
    if not buyer_name.strip():
        st.error("Preencha seu nome.")
        return
    if not buyer_phone.strip():
        st.error("Preencha seu telefone com DDD.")
        return
    if proof_file is None:
        st.error("Anexe o comprovante de pagamento.")
        return

    with st.spinner("Enviando comprovante..."):
        proof_url = upload_proof(raffle["id"], selected_nums[0], proof_file)
        reserve_tickets(
            raffle["id"], selected_nums, buyer_name.strip(),
            buyer_phone.strip(), proof_url,
        )
        _load_tickets.clear()
        _load_raffle.clear()

    st.success(
        f"Número(s) **{format_numbers_list(selected_nums)}** reservado(s) "
        "com sucesso! Aguarde a confirmação do pagamento."
    )
    st.rerun()


# ── Fluxo principal ──────────────────────────────────────────────────────────
def main() -> None:
    st.markdown("# :wheelchair: Rifa Amiga")

    raffle = _load_raffle()
    if raffle is None:
        st.info("Nenhuma rifa ativa no momento. Volte mais tarde!")
        st.stop()

    _show_raffle_header(raffle)
    _show_winner_banner(raffle)

    st.divider()
    render_legend()

    tickets = _load_tickets(raffle["id"])
    render_number_grid(tickets)

    if raffle.get("winner_number") is None:
        available = [t["number"] for t in tickets if t["status"] == "available"]
        if not available:
            st.warning("Todos os números já foram reservados ou confirmados!")
        else:
            _show_reservation_form(raffle, available)

    render_footer()


main()
