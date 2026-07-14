# TX RetailOS — Current Architecture (MVP)

TX RetailOS is a single centralized system. One backend, one SQLite
database, one source of truth. There is no offline mode, no sync engine,
and no multi-device conflict resolution in the current build.

Flow: Frontend → API → Database → Response — every request updates the
database immediately and returns the current state. What you see is
always current.

**Offline Mode & Sync (Coming Soon):** the codebase reserves structure
for this (a feature flag, an unused client-side queue module, and
disabled sync/conflict endpoints) but none of it is active. Do not
document or promise sync behavior until `SYNC_ENABLED=True` ships.