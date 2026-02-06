# Rifa Amiga

App Streamlit para gerenciar rifas solidárias com confirmação de pagamento via comprovante.

## Requisitos

- Python 3.8+
- Conta no [Supabase](https://supabase.com) (gratuito)

## Setup Local

### 1. Configure o Supabase

- Crie um projeto em [supabase.com](https://supabase.com)
- No **SQL Editor**, cole e execute o conteúdo de `supabase_setup.sql`
- Em **Authentication > Users**, crie um usuário (email/senha) para a admin
- Em **Settings > API**, copie:
  - Project URL
  - anon public key

### 2. Crie um Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure os Secrets do Streamlit

Crie o arquivo `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "eyJ..."
```

(Cole a URL e a anon key que copiou)

### 5. Rode o app

```bash
streamlit run app.py
```

Acesse em `http://localhost:8501`

## Fluxo de Uso

1. **Admin** (página "Painel Admin"):
   - Login com email/senha
   - Criar rifa (título, quantidade de números, valor, chave PIX)
   - Confirmar/rejeitar reservas validando comprovantes
   - Sortear vencedor

2. **Público** (página "Rifa"):
   - Ver grade de números
   - Selecionar número disponível
   - Preencher nome e anexar comprovante PIX
   - Número fica reservado aguardando confirmação

## Deploy no Streamlit Cloud

1. Suba o repo para GitHub
2. Connect ao repo em [streamlit.io/cloud](https://streamlit.io/cloud)
3. Em **Settings > Secrets**, adicione:
   ```toml
   SUPABASE_URL = "..."
   SUPABASE_KEY = "..."
   ```

## Deactivar o venv

```bash
deactivate
```
