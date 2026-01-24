# PostgreSQL Connection Timeout Issues

## Problem Description

Users experiencing intermittent connection timeout errors when connecting to PostgreSQL database from the application server. Error message: `FATAL: remaining connection slots are reserved for non-replication superuser connections`.

## Symptoms

- Application throws connection errors during peak hours
- `pg_stat_activity` shows many idle connections
- Max connections limit being reached
- Response times increase significantly

## Root Causes

### 1. Connection Pool Misconfiguration

The connection pool may not be releasing connections properly:

```python
# Bad - no connection pooling
conn = psycopg2.connect(DATABASE_URL)

# Good - use SQLAlchemy with pooling
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
```

### 2. Max Connections Too Low

Check current settings:

```sql
SHOW max_connections;
```

Default is often 100, which may be insufficient for production workloads.

### 3. Idle Connection Timeout

Connections may be held open unnecessarily:

```sql
-- Check idle connections
SELECT pid, usename, state, state_change 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND state_change < current_timestamp - interval '5 minutes';
```

## Solutions

### Increase Max Connections

Edit `postgresql.conf`:

```
max_connections = 200
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### Configure Connection Pooling

Use PgBouncer as a connection pooler:

```ini
[databases]
mydb = host=localhost port=5432 dbname=mydb

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

### Application-Level Fixes

1. Use connection pooling in your application
2. Set proper timeout values
3. Close connections when done
4. Use context managers

```python
with engine.connect() as conn:
    result = conn.execute(query)
    # Connection automatically returned to pool
```

### Implement Connection Limits

Set per-role connection limits:

```sql
ALTER ROLE myapp CONNECTION LIMIT 50;
```

## Prevention

- Monitor connection count with alerts
- Implement proper connection lifecycle management
- Use connection poolers in production
- Regular review of `pg_stat_activity`
- Load testing before production deployment

## Related Issues

- [Slow Query Performance](#)
- [Database Migration Best Practices](#)
- [Connection Pool Configuration Guide](#)
