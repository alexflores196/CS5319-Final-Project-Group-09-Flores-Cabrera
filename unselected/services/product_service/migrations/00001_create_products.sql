-- Owned by product-service: catalog and inventory
CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    category VARCHAR(100) DEFAULT 'General',
    price_in_cents INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    image_url VARCHAR(1024),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
