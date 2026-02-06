-- =============================================================================
-- Rifa Amiga — SQL para rodar no Supabase SQL Editor
-- =============================================================================

-- 1. Tabela de rifas
create table if not exists public.raffles (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    description text default '',
    total_numbers int not null,
    price numeric(10,2) not null default 10.00,
    pix_key text not null default '',
    pix_name text not null default '',
    status text not null default 'active' check (status in ('active', 'finished')),
    winner_number int,
    created_at timestamptz not null default now()
);

-- 2. Tabela de tickets (numeros da rifa)
create table if not exists public.tickets (
    id uuid primary key default gen_random_uuid(),
    raffle_id uuid not null references public.raffles(id) on delete cascade,
    number int not null,
    status text not null default 'available' check (status in ('available', 'reserved', 'confirmed')),
    buyer_name text,
    buyer_phone text,
    proof_url text,
    reserved_at timestamptz,
    confirmed_at timestamptz,
    unique(raffle_id, number)
);

-- 3. Indices para performance
create index if not exists idx_tickets_raffle_id on public.tickets(raffle_id);
create index if not exists idx_tickets_status on public.tickets(status);

-- 4. RLS (Row Level Security) — desabilitar para simplificar
--    Em producao, configure policies adequadas.
alter table public.raffles enable row level security;
alter table public.tickets enable row level security;

-- Policy: permitir leitura publica
create policy "Leitura publica de raffles"
    on public.raffles for select
    using (true);

create policy "Leitura publica de tickets"
    on public.tickets for select
    using (true);

-- Policy: permitir insercao/atualizacao via service role (o Streamlit usa a anon key,
-- entao precisamos de policies mais abertas para insert/update)
create policy "Insert tickets anonimo"
    on public.tickets for insert
    with check (true);

create policy "Update tickets anonimo"
    on public.tickets for update
    using (true);

create policy "Insert raffles anonimo"
    on public.raffles for insert
    with check (true);

create policy "Update raffles anonimo"
    on public.raffles for update
    using (true);

-- =============================================================================
-- 5. Storage bucket para comprovantes
-- Rode este comando no SQL Editor OU crie manualmente pelo Dashboard:
--    Storage > New bucket > Nome: "proofs" > Marcar como Public
-- =============================================================================
insert into storage.buckets (id, name, public)
values ('proofs', 'proofs', true)
on conflict (id) do nothing;

-- Policy de upload publico no bucket proofs
create policy "Upload publico proofs"
    on storage.objects for insert
    with check (bucket_id = 'proofs');

-- Policy de leitura publica no bucket proofs
create policy "Leitura publica proofs"
    on storage.objects for select
    using (bucket_id = 'proofs');
