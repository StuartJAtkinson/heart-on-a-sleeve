-- Heart on a Sleeve — Full Schema
-- Run after 01-init.sql

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);

-- Design projects (bbox stored as floats for simple ORM access)
CREATE TABLE design_projects (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    merch_type VARCHAR(50) NOT NULL,
    bbox_west FLOAT NOT NULL,
    bbox_south FLOAT NOT NULL,
    bbox_east FLOAT NOT NULL,
    bbox_north FLOAT NOT NULL,
    style VARCHAR(50) DEFAULT 'osm_default',
    coaster_shape VARCHAR(50),
    palette_overrides JSONB,
    include_labels BOOLEAN DEFAULT TRUE,
    include_buildings BOOLEAN DEFAULT TRUE,
    svg_url VARCHAR(500),
    stl_buildings_url VARCHAR(500),
    stl_land_url VARCHAR(500),
    stl_water_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_design_projects_user ON design_projects(user_id);

-- OSM data cache (24 hr TTL, spatial index for bbox overlap queries)
CREATE TABLE osm_data_cache (
    id SERIAL PRIMARY KEY,
    bbox GEOMETRY(POLYGON, 4326) NOT NULL,
    zoom_level INT NOT NULL,
    raw_json JSONB NOT NULL,
    element_count INT NOT NULL,
    license_info JSONB NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);
CREATE INDEX idx_osm_cache_bbox ON osm_data_cache USING GIST(bbox);
CREATE INDEX idx_osm_cache_expires ON osm_data_cache (expires_at);

-- POD orders
CREATE TABLE pod_orders (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES design_projects(id),
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL,
    external_order_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    product_sku VARCHAR(255),
    quantity INT DEFAULT 1,
    price_gbp NUMERIC(10, 2),
    tracking_number VARCHAR(255),
    tracking_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- License audit trail
CREATE TABLE license_audit (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES design_projects(id),
    data_source VARCHAR(100) NOT NULL,
    license_type VARCHAR(50) NOT NULL,
    attribution_text TEXT,
    compliant BOOLEAN DEFAULT TRUE,
    checked_at TIMESTAMP DEFAULT NOW()
);
