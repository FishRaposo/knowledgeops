# Database Migrations

KnowledgeOps tracks schema state in the `schema_versions` table.

Local Docker startup applies `infra/postgres/init.sql`, which creates the initial schema and inserts version `001_initial`.

For an existing database, apply migrations in lexical order:

```bash
psql "$DATABASE_URL" -f infra/postgres/migrations/001_initial.sql
```

Future migrations must:

- Be named `NNN_description.sql`.
- Be idempotent with `IF NOT EXISTS` or equivalent guards.
- Insert their version into `schema_versions`.
- Avoid destructive changes unless a matching rollback note is documented.
