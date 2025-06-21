# Database Migrations

This directory contains database migrations for the MedixAI project using Alembic.

## Migration Commands

### Create a New Migration

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration
alembic revision -m "description of changes"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +1

# Rollback specific number of migrations
alembic downgrade -1

# Rollback all migrations
alembic downgrade base
```

### Migration Status

```bash
# Show current migration version
alembic current

# Show migration history
alembic history --verbose
```

## Migration Guidelines

1. Always review auto-generated migrations before applying them
2. Test migrations in development environment first
3. Backup database before applying migrations in production
4. Include both upgrade and downgrade operations
5. Use meaningful migration names
6. Keep migrations atomic and focused

## Initial Setup

1. Update database URL in `alembic.ini` or use environment variables
2. Run `alembic upgrade head` to apply all migrations
3. Verify database schema matches expected state

## Troubleshooting

If you encounter issues:

1. Check database connection settings
2. Verify alembic version history is intact
3. Review migration logs
4. Ensure all model changes are imported in `env.py`

## Best Practices

1. Never modify existing migrations
2. Always create new migrations for changes
3. Test both upgrade and downgrade paths
4. Keep migrations reversible when possible
5. Document complex migrations
6. Use transactions for data migrations 