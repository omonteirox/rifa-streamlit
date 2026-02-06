"""Componentes visuais reutilizáveis (HTML/Streamlit)."""

from __future__ import annotations

from typing import Any

import streamlit as st

type TicketDict = dict[str, Any]


def render_number_grid(tickets: list[TicketDict]) -> None:
    """Renderiza a grade visual dos números da rifa."""
    cells = "".join(
        f'<div class="num-btn num-{t["status"]}">{t["number"]:02d}</div>'
        for t in tickets
    )
    st.markdown(f'<div class="number-grid">{cells}</div>', unsafe_allow_html=True)


def render_legend() -> None:
    """Renderiza a legenda de cores (disponível / reservado / confirmado)."""
    st.markdown(
        """
        <div class="legend">
            <span class="legend-item">
                <span class="legend-dot" style="background:#2ecc71"></span> Disponível
            </span>
            <span class="legend-item">
                <span class="legend-dot" style="background:#f1c40f"></span> Reservado
            </span>
            <span class="legend-item">
                <span class="legend-dot" style="background:#3498db"></span> Confirmado
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pix_box(pix_name: str, pix_key: str) -> None:
    """Renderiza a caixa com dados PIX."""
    st.markdown(
        f"""
        <div class="pix-box">
            <div class="pix-name">{pix_name}</div>
            <div class="pix-key">{pix_key}</div>
            <small>Chave PIX — copie e faça o pagamento</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_number(n: int) -> str:
    """Formata um número para exibição (ex: 07, 42)."""
    return f"{n:02d}"


def format_numbers_list(numbers: list[int]) -> str:
    """Formata lista de números para exibição (ex: '01, 07, 42')."""
    return ", ".join(format_number(n) for n in numbers)


def render_footer() -> None:
    """Renderiza o rodapé com créditos do desenvolvedor."""
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 24px 0 12px;
            margin-top: 40px;
            border-top: 1px solid #333;
            color: #888;
            font-size: 0.8rem;
        ">
            Desenvolvido por: <strong>Gustavo Monteiro</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
