-- ==============================================================================
-- FattoAMano Database Schema & Supabase Configuration
-- E-commerce Boutique per Bracciali in Rame Fatti a Mano (99.9% Rame Puro)
-- ==============================================================================

-- 1. Tabella Prodotti
CREATE TABLE IF NOT EXISTS public.fattoamano_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    image_url TEXT NOT NULL,
    purity TEXT DEFAULT '99.9% Rame Puro',
    details TEXT,
    stripe_product_id TEXT,
    stripe_price_id TEXT,
    category TEXT DEFAULT 'Intrecciati',
    in_stock BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. Indici per prestazioni
CREATE INDEX IF NOT EXISTS idx_fattoamano_products_created_at ON public.fattoamano_products (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fattoamano_products_category ON public.fattoamano_products (category);

-- 3. Row Level Security (RLS)
ALTER TABLE public.fattoamano_products ENABLE ROW LEVEL SECURITY;

-- Consentire lettura pubblica dei prodotti disponibili
DROP POLICY IF EXISTS "Public can view active products" ON public.fattoamano_products;
CREATE POLICY "Public can view active products"
    ON public.fattoamano_products
    FOR SELECT
    USING (in_stock = true);

-- Consentire inserimento e modifica agli utenti autenticati o via service_role (usato dal bot Telegram)
DROP POLICY IF EXISTS "Full access for service role and admin" ON public.fattoamano_products;
CREATE POLICY "Full access for service role and admin"
    ON public.fattoamano_products
    FOR ALL
    USING (auth.role() = 'service_role' OR auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

-- 4. Storage Bucket per foto prodotti da Telegram
-- Il bucket deve chiamarsi: fattoamano-products (public bucket)
INSERT INTO storage.buckets (id, name, public)
VALUES ('fattoamano-products', 'fattoamano-products', true)
ON CONFLICT (id) DO NOTHING;

-- Policy di lettura pubblica per lo storage bucket
CREATE POLICY "Public Access Bucket fattoamano-products"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'fattoamano-products');

-- Policy di upload per service role
CREATE POLICY "Service Role Upload to fattoamano-products"
    ON storage.objects FOR INSERT
    WITH CHECK (bucket_id = 'fattoamano-products');
