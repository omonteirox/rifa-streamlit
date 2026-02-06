import random
from datetime import datetime, timezone

import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(page_title="Admin — Rifa Amiga", page_icon=":lock:", layout="wide")
st.markdown(
    "<style>#MainMenu{visibility:hidden;}footer{visibility:hidden;}</style>",
    unsafe_allow_html=True,
)

sb = get_supabase()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "admin_session" not in st.session_state:
    st.session_state["admin_session"] = None

if st.session_state["admin_session"] is None:
    st.markdown("## :lock: Login do Administrador")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        login = st.form_submit_button("Entrar", use_container_width=True)

        if login:
            try:
                resp = sb.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                st.session_state["admin_session"] = resp.session
                st.rerun()
            except Exception as e:
                st.error(f"Falha no login: {e}")
    st.stop()

# ── Logado ───────────────────────────────────────────────────────────────────
st.markdown("## :shield: Painel Administrativo")

if st.sidebar.button("Sair"):
    st.session_state["admin_session"] = None
    st.rerun()


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_active_raffle():
    res = sb.table("raffles").select("*").eq("status", "active").limit(1).execute()
    return res.data[0] if res.data else None


def get_all_tickets(raffle_id: str):
    res = (
        sb.table("tickets")
        .select("*")
        .eq("raffle_id", raffle_id)
        .order("number")
        .execute()
    )
    return res.data


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
raffle = get_active_raffle()

tab_config, tab_reservas, tab_confirmar_manual, tab_sorteio, tab_visao = st.tabs(
    ["Configuracao", "Reservas pendentes", "Confirmar manual", "Sorteio", "Visao geral"]
)

# ── TAB: Configuracao ────────────────────────────────────────────────────────
with tab_config:
    if raffle is None:
        st.info("Nenhuma rifa ativa. Crie uma abaixo.")
        with st.form("create_raffle"):
            title = st.text_input("Titulo da rifa", value="Rifa Solidaria — Cadeira de Rodas")
            description = st.text_area("Descricao")
            total_numbers = st.number_input(
                "Quantidade de numeros", min_value=10, max_value=1000, value=100, step=10
            )
            price = st.number_input("Valor por numero (R$)", min_value=0.5, value=10.0, step=0.5)
            pix_key = st.text_input("Chave PIX")
            pix_name = st.text_input("Nome do titular da chave PIX")
            create = st.form_submit_button("Criar rifa", use_container_width=True)

            if create:
                if not title.strip() or not pix_key.strip():
                    st.error("Preencha titulo e chave PIX.")
                else:
                    with st.spinner("Criando rifa..."):
                        new_raffle = (
                            sb.table("raffles")
                            .insert(
                                {
                                    "title": title.strip(),
                                    "description": description.strip(),
                                    "total_numbers": int(total_numbers),
                                    "price": float(price),
                                    "pix_key": pix_key.strip(),
                                    "pix_name": pix_name.strip(),
                                    "status": "active",
                                }
                            )
                            .execute()
                        )
                        raffle_id = new_raffle.data[0]["id"]

                        # Gerar tickets em lote
                        tickets_batch = [
                            {
                                "raffle_id": raffle_id,
                                "number": i,
                                "status": "available",
                            }
                            for i in range(int(total_numbers))
                        ]
                        # Inserir em blocos de 500 (limite Supabase)
                        for start in range(0, len(tickets_batch), 500):
                            chunk = tickets_batch[start : start + 500]
                            sb.table("tickets").insert(chunk).execute()

                    st.success(f"Rifa criada com {int(total_numbers)} numeros!")
                    st.rerun()
    else:
        st.subheader(f"Rifa ativa: {raffle['title']}")
        with st.form("edit_raffle"):
            new_title = st.text_input("Titulo", value=raffle["title"])
            new_desc = st.text_area("Descricao", value=raffle.get("description", ""))
            new_price = st.number_input(
                "Valor por numero (R$)",
                min_value=0.5,
                value=float(raffle["price"]),
                step=0.5,
            )
            new_pix = st.text_input("Chave PIX", value=raffle.get("pix_key", ""))
            new_pix_name = st.text_input("Nome do titular da chave PIX", value=raffle.get("pix_name", ""))
            save = st.form_submit_button("Salvar alteracoes", use_container_width=True)

            if save:
                sb.table("raffles").update(
                    {
                        "title": new_title.strip(),
                        "description": new_desc.strip(),
                        "price": float(new_price),
                        "pix_key": new_pix.strip(),
                        "pix_name": new_pix_name.strip(),
                    }
                ).eq("id", raffle["id"]).execute()
                st.success("Rifa atualizada!")
                st.rerun()

# ── TAB: Reservas pendentes ──────────────────────────────────────────────────
with tab_reservas:
    if raffle is None:
        st.warning("Crie uma rifa primeiro.")
    else:
        reserved = (
            sb.table("tickets")
            .select("*")
            .eq("raffle_id", raffle["id"])
            .eq("status", "reserved")
            .order("number")
            .execute()
            .data
        )

        if not reserved:
            st.info("Nenhuma reserva pendente.")
        else:
            st.markdown(f"**{len(reserved)}** reserva(s) pendente(s)")

            col_all_confirm, col_all_reject = st.columns(2)
            with col_all_confirm:
                if st.button("Confirmar todas", use_container_width=True, type="primary"):
                    for ticket in reserved:
                        sb.table("tickets").update(
                            {
                                "status": "confirmed",
                                "confirmed_at": datetime.now(timezone.utc).isoformat(),
                            }
                        ).eq("id", ticket["id"]).execute()
                    st.success(f"{len(reserved)} reserva(s) confirmada(s)!")
                    st.rerun()

            with col_all_reject:
                if st.button("Rejeitar todas", use_container_width=True, type="secondary"):
                    for ticket in reserved:
                        sb.table("tickets").update(
                            {
                                "status": "available",
                                "buyer_name": None,
                                "proof_url": None,
                                "reserved_at": None,
                            }
                        ).eq("id", ticket["id"]).execute()
                    st.warning(f"{len(reserved)} reserva(s) rejeitada(s).")
                    st.rerun()

            st.divider()

            for ticket in reserved:
                with st.expander(
                    f"Numero {ticket['number']:02d} — {ticket.get('buyer_name', 'Sem nome')}",
                    expanded=False,
                ):
                    st.write(f"**Nome:** {ticket.get('buyer_name', '-')}")
                    st.write(f"**Reservado em:** {ticket.get('reserved_at', '-')}")

                    proof = ticket.get("proof_url")
                    if proof:
                        st.image(proof, caption="Comprovante", width=400)
                    else:
                        st.warning("Sem comprovante anexado.")

                    col_confirm, col_reject = st.columns(2)
                    with col_confirm:
                        if st.button(
                            "Confirmar",
                            key=f"confirm_{ticket['number']}",
                            use_container_width=True,
                        ):
                            sb.table("tickets").update(
                                {
                                    "status": "confirmed",
                                    "confirmed_at": datetime.now(timezone.utc).isoformat(),
                                }
                            ).eq("id", ticket["id"]).execute()
                            st.success(f"Numero {ticket['number']:02d} confirmado!")
                            st.rerun()

                    with col_reject:
                        if st.button(
                            "Rejeitar",
                            key=f"reject_{ticket['number']}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            sb.table("tickets").update(
                                {
                                    "status": "available",
                                    "buyer_name": None,
                                    "proof_url": None,
                                    "reserved_at": None,
                                }
                            ).eq("id", ticket["id"]).execute()
                            st.warning(f"Numero {ticket['number']:02d} liberado.")
                            st.rerun()

# ── TAB: Confirmar manual ────────────────────────────────────────────────────
with tab_confirmar_manual:
    if raffle is None:
        st.warning("Crie uma rifa primeiro.")
    else:
        st.markdown(
            "Use esta aba para confirmar numeros de quem pagou presencialmente, "
            "sem precisar de comprovante."
        )
        all_tickets = get_all_tickets(raffle["id"])
        available_numbers = [t for t in all_tickets if t["status"] == "available"]

        if not available_numbers:
            st.info("Nenhum numero disponivel.")
        else:
            with st.form("manual_confirm"):
                options = [f"{t['number']:02d}" for t in available_numbers]
                selected = st.selectbox("Numero", options)
                buyer = st.text_input("Nome do comprador")
                confirm = st.form_submit_button(
                    "Confirmar numero", use_container_width=True
                )

                if confirm:
                    if not buyer.strip():
                        st.error("Preencha o nome do comprador.")
                    else:
                        num = int(selected)
                        sb.table("tickets").update(
                            {
                                "status": "confirmed",
                                "buyer_name": buyer.strip(),
                                "confirmed_at": datetime.now(timezone.utc).isoformat(),
                            }
                        ).eq("raffle_id", raffle["id"]).eq("number", num).execute()
                        st.success(f"Numero {num:02d} confirmado para {buyer.strip()}!")
                        st.rerun()

# ── TAB: Sorteio ─────────────────────────────────────────────────────────────
with tab_sorteio:
    if raffle is None:
        st.warning("Crie uma rifa primeiro.")
    elif raffle.get("winner_number") is not None:
        st.balloons()
        winner_ticket = (
            sb.table("tickets")
            .select("*")
            .eq("raffle_id", raffle["id"])
            .eq("number", raffle["winner_number"])
            .limit(1)
            .execute()
            .data
        )
        winner_name = winner_ticket[0].get("buyer_name", "-") if winner_ticket else "-"
        st.success(
            f"Numero sorteado: **{raffle['winner_number']:02d}** — "
            f"Ganhador(a): **{winner_name}**"
        )
    else:
        confirmed = (
            sb.table("tickets")
            .select("number, buyer_name")
            .eq("raffle_id", raffle["id"])
            .eq("status", "confirmed")
            .execute()
            .data
        )

        if not confirmed:
            st.warning("Nenhum numero confirmado ainda. Confirme pagamentos primeiro.")
        else:
            st.info(f"**{len(confirmed)}** numero(s) confirmado(s) participando do sorteio.")
            st.markdown("---")

            if st.button("SORTEAR", use_container_width=True, type="primary"):
                winner = random.choice(confirmed)
                sb.table("raffles").update(
                    {
                        "winner_number": winner["number"],
                        "status": "finished",
                    }
                ).eq("id", raffle["id"]).execute()
                st.balloons()
                st.success(
                    f"Numero sorteado: **{winner['number']:02d}** — "
                    f"Ganhador(a): **{winner.get('buyer_name', '-')}**"
                )
                st.rerun()

# ── TAB: Visao geral ─────────────────────────────────────────────────────────
with tab_visao:
    if raffle is None:
        st.warning("Crie uma rifa primeiro.")
    else:
        all_t = get_all_tickets(raffle["id"])
        total = len(all_t)
        avail = sum(1 for t in all_t if t["status"] == "available")
        reserv = sum(1 for t in all_t if t["status"] == "reserved")
        conf = sum(1 for t in all_t if t["status"] == "confirmed")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", total)
        c2.metric("Disponiveis", avail)
        c3.metric("Reservados", reserv)
        c4.metric("Confirmados", conf)

        arrecadado = conf * float(raffle["price"])
        esperado = total * float(raffle["price"])
        st.metric("Valor arrecadado (confirmados)", f"R$ {arrecadado:.2f}")
        st.progress(conf / total if total > 0 else 0, text=f"{conf}/{total} confirmados")

        st.divider()

        # Tabela de todos os tickets nao-disponiveis
        sold = [t for t in all_t if t["status"] != "available"]
        if sold:
            import pandas as pd

            df = pd.DataFrame(sold)[["number", "status", "buyer_name", "reserved_at", "confirmed_at"]]
            df.columns = ["Numero", "Status", "Nome", "Reservado em", "Confirmado em"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum numero vendido ainda.")
