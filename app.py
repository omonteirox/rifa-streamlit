import streamlit as st
from utils.supabase_client import get_supabase
from utils.storage import upload_proof
from datetime import datetime, timezone

st.set_page_config(
    page_title="Rifa Amiga",
    page_icon=":wheelchair:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem;}

    .number-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 6px;
        max-width: 700px;
        margin: 0 auto;
    }
    @media (max-width: 600px) {
        .number-grid { grid-template-columns: repeat(5, 1fr); }
    }
    .num-btn {
        border: none;
        border-radius: 8px;
        padding: 12px 0;
        font-size: 1rem;
        font-weight: 700;
        text-align: center;
        color: #fff;
    }
    .num-available {background: #2ecc71;}
    .num-reserved {background: #f1c40f; color: #333;}
    .num-confirmed {background: #3498db;}

    .legend {display:flex; gap:18px; justify-content:center; margin:12px 0 20px; flex-wrap:wrap;}
    .legend-item {display:flex; align-items:center; gap:5px; font-size:.9rem;}
    .legend-dot {width:16px;height:16px;border-radius:4px;display:inline-block;}

    .pix-box {
        background: #1A1F2E;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        margin: 10px 0;
    }
    .pix-box .pix-name {font-size: 1.1rem; font-weight: 600; margin-bottom: 4px;}
    .pix-box .pix-key {font-family: monospace; font-size: 1rem; color: #2ecc71;}
    </style>
    """,
    unsafe_allow_html=True,
)

sb = get_supabase()


# ── Helpers ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_active_raffle():
    res = sb.table("raffles").select("*").eq("status", "active").limit(1).execute()
    return res.data[0] if res.data else None


@st.cache_data(ttl=5)
def load_tickets(raffle_id: str):
    res = (
        sb.table("tickets")
        .select("number, status, buyer_name")
        .eq("raffle_id", raffle_id)
        .order("number")
        .execute()
    )
    return res.data


def reserve_tickets(raffle_id: str, numbers: list[int], buyer_name: str, proof_url: str):
    now = datetime.now(timezone.utc).isoformat()
    for number in numbers:
        sb.table("tickets").update(
            {
                "status": "reserved",
                "buyer_name": buyer_name,
                "proof_url": proof_url,
                "reserved_at": now,
            }
        ).eq("raffle_id", raffle_id).eq("number", number).eq("status", "available").execute()


# ── Pagina ───────────────────────────────────────────────────────────────────
st.markdown("# :wheelchair: Rifa Amiga")

raffle = load_active_raffle()

if raffle is None:
    st.info("Nenhuma rifa ativa no momento. Volte mais tarde!")
    st.stop()

# Info da rifa
st.markdown(f"### {raffle['title']}")
if raffle.get("description"):
    st.markdown(raffle["description"])

col1, col2 = st.columns(2)
col1.metric("Valor por numero", f"R$ {float(raffle['price']):.2f}")

pix_name = raffle.get("pix_name", "")
pix_key = raffle.get("pix_key", "")
col2.markdown(
    f"""
    <div class="pix-box">
        <div class="pix-name">{pix_name}</div>
        <div class="pix-key">{pix_key}</div>
        <small>Chave PIX — copie e faça o pagamento</small>
    </div>
    """,
    unsafe_allow_html=True,
)

# Verificar se ja houve sorteio
if raffle.get("winner_number") is not None:
    st.balloons()
    st.success(
        f"Rifa encerrada! Numero sorteado: **{raffle['winner_number']}**"
    )

st.divider()

# Legenda
st.markdown(
    """
    <div class="legend">
        <span class="legend-item"><span class="legend-dot" style="background:#2ecc71"></span> Disponivel</span>
        <span class="legend-item"><span class="legend-dot" style="background:#f1c40f"></span> Reservado</span>
        <span class="legend-item"><span class="legend-dot" style="background:#3498db"></span> Confirmado</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Carregar tickets
tickets = load_tickets(raffle["id"])

# ── Grade de numeros (HTML puro) ─────────────────────────────────────────────
grid_html = '<div class="number-grid">'
for ticket in tickets:
    css_class = f"num-{ticket['status']}"
    grid_html += f'<div class="num-btn {css_class}">{ticket["number"]:02d}</div>'
grid_html += "</div>"
st.markdown(grid_html, unsafe_allow_html=True)

# ── Selecao de numeros ───────────────────────────────────────────────────────
if raffle.get("winner_number") is None:
    available_numbers = [t["number"] for t in tickets if t["status"] == "available"]

    if not available_numbers:
        st.warning("Todos os numeros ja foram reservados ou confirmados!")
    else:
        st.divider()
        st.subheader("Escolha seu(s) numero(s)")

        options = [f"{n:02d}" for n in available_numbers]
        selected = st.multiselect(
            "Selecione um ou mais numeros disponiveis",
            options,
            placeholder="Clique para escolher...",
        )

        if selected:
            selected_nums = [int(s) for s in selected]
            total = len(selected_nums) * float(raffle["price"])
            st.info(
                f"**{len(selected_nums)}** numero(s) selecionado(s) — "
                f"Total: **R$ {total:.2f}**"
            )

            with st.form("reserve_form"):
                buyer_name = st.text_input("Seu nome completo")
                proof_file = st.file_uploader(
                    "Comprovante de pagamento (imagem)",
                    type=["png", "jpg", "jpeg", "webp"],
                )
                submitted = st.form_submit_button(
                    "Enviar e reservar", use_container_width=True
                )

                if submitted:
                    if not buyer_name.strip():
                        st.error("Preencha seu nome.")
                    elif proof_file is None:
                        st.error("Anexe o comprovante de pagamento.")
                    else:
                        with st.spinner("Enviando comprovante..."):
                            proof_url = upload_proof(
                                raffle["id"], selected_nums[0], proof_file
                            )
                            reserve_tickets(
                                raffle["id"],
                                selected_nums,
                                buyer_name.strip(),
                                proof_url,
                            )
                            load_tickets.clear()
                            load_active_raffle.clear()

                        nums_str = ", ".join(f"{n:02d}" for n in selected_nums)
                        st.success(
                            f"Numero(s) **{nums_str}** reservado(s) com sucesso! "
                            "Aguarde a confirmacao do pagamento."
                        )
                        st.rerun()
