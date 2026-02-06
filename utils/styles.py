"""Estilos CSS reutilizáveis da aplicação."""

# ── Base compartilhada ───────────────────────────────────────────────────────
_BASE_RESET = """
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Viewport / touch */
html {-webkit-text-size-adjust: 100%;}
* {-webkit-tap-highlight-color: transparent;}
input, button, select, textarea {font-size: 16px !important;}  /* evita zoom no iOS */
"""

_RESPONSIVE_STREAMLIT = """
/* ── Streamlit overrides para mobile ───────────── */
@media (max-width: 640px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 0.5rem !important;
    }
    /* Tabs menores no mobile */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 6px;
        font-size: 0.78rem;
    }
    /* Metrics lado a lado sem overflow */
    [data-testid="stMetric"] {
        padding: 8px 4px;
    }
    [data-testid="stMetric"] label {
        font-size: 0.75rem;
    }
}
"""

HIDE_STREAMLIT_CHROME = f"""
<style>
{_BASE_RESET}
{_RESPONSIVE_STREAMLIT}
</style>
"""

MAIN_PAGE_CSS = f"""
<style>
{_BASE_RESET}
.block-container {{padding-top: 1rem;}}

/* ── Grade de números (mobile-first) ───────────── */
.number-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 6px;
    max-width: 700px;
    margin: 0 auto;
    padding: 0 4px;
}}
.num-btn {{
    border: none;
    border-radius: 8px;
    padding: 14px 0;
    min-height: 44px;          /* touch target mínimo */
    font-size: 0.95rem;
    font-weight: 700;
    text-align: center;
    color: #fff;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.num-available  {{background: #2ecc71;}}
.num-reserved   {{background: #f1c40f; color: #333;}}
.num-confirmed  {{background: #3498db;}}

/* Tablet+ */
@media (min-width: 481px) {{
    .number-grid {{ grid-template-columns: repeat(8, 1fr); gap: 7px; }}
}}
/* Desktop */
@media (min-width: 769px) {{
    .number-grid {{ grid-template-columns: repeat(10, 1fr); gap: 8px; }}
    .num-btn {{ padding: 12px 0; font-size: 1rem; }}
}}

/* ── Legenda ───────────────────────────────────── */
.legend {{
    display: flex;
    gap: 14px;
    justify-content: center;
    margin: 10px 0 16px;
    flex-wrap: wrap;
}}
.legend-item {{display: flex; align-items: center; gap: 5px; font-size: .85rem;}}
.legend-dot  {{width: 14px; height: 14px; border-radius: 4px; display: inline-block;}}

/* ── Caixa PIX ─────────────────────────────────── */
.pix-box {{
    background: #1A1F2E;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 14px 12px;
    text-align: center;
    margin: 10px 0;
    word-break: break-all;     /* chave PIX não estoura */
    overflow-wrap: anywhere;
}}
.pix-box .pix-name {{font-size: 1rem; font-weight: 600; margin-bottom: 4px;}}
.pix-box .pix-key  {{font-family: monospace; font-size: 0.85rem; color: #2ecc71;}}
@media (min-width: 769px) {{
    .pix-box .pix-key {{ font-size: 1rem; }}
}}

{_RESPONSIVE_STREAMLIT}
</style>
"""
