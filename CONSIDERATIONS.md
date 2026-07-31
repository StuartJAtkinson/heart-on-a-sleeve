# Considerations

- Alembic is now set up (`backend/alembic/`, baseline migration `f652273fd930`) and verified by `backend/tests/test_alembic_migrations.py`, but `backend/app/api/router.py`'s `lifespan()` still bootstraps the schema via `Base.metadata.create_all` plus an ad-hoc `ALTER TABLE ... ADD COLUMN` loop rather than `alembic upgrade head`. Swapping that in touches how the live Cloud Run service (backed by production Postgres/PostGIS) bootstraps its schema on every deploy, so it's left for a human to review and wire up deliberately rather than changed unattended.
