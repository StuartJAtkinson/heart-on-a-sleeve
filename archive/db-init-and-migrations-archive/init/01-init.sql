-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Grant
GRANT ALL PRIVILEGES ON DATABASE heart_on_a_sleeve TO heart_user;