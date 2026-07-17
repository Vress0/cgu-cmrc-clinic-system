# Backup And Restore

## Backup

Create a PostgreSQL custom-format dump from the running Docker database:

```powershell
docker compose exec -T postgres pg_dump -U clinic -d clinic -Fc > backup-clinic.dump
```

Production backups should include:

- Database dump
- Application commit SHA
- Alembic revision
- Environment variable inventory without secrets
- Backup timestamp and operator

Do not commit backup files to Git.

## Restore Verification

Restore into a temporary database:

```powershell
docker compose exec -T postgres createdb -U clinic clinic_restore_check
Get-Content .\backup-clinic.dump -AsByteStream | docker compose exec -T postgres pg_restore -U clinic -d clinic_restore_check --no-owner
docker compose exec -T postgres psql -U clinic -d clinic_restore_check -c "select count(*) from patients;"
docker compose exec -T postgres dropdb -U clinic clinic_restore_check
```

Verify:

- Alembic version table exists and reports the expected head.
- Core tables are present.
- Patient, visit, prescription, dispensing, inventory, and audit tables can be queried.
- Row counts are plausible.
- No backup artifact remains in the repository.

## Operational Notes

- Store production backups in encrypted storage.
- Restrict restore permissions to administrators.
- Test restore procedures before the first real clinic event.
- Keep backup retention and deletion policy documented outside the application repo.
