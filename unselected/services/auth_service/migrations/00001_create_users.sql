-- Owned by auth-service: users table supporting RBAC (customer vs admin)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'customer', -- 'customer' or 'admin'
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
