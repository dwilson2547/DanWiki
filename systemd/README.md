# Production Systemd Service Files

## Installation

### 1. Copy service files

```bash
sudo cp systemd/wiki-worker@.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 2. Start workers

```bash
# Start multiple workers (e.g., 4 workers)
sudo systemctl enable wiki-worker@1
sudo systemctl enable wiki-worker@2
sudo systemctl enable wiki-worker@3
sudo systemctl enable wiki-worker@4

sudo systemctl start wiki-worker@1
sudo systemctl start wiki-worker@2
sudo systemctl start wiki-worker@3
sudo systemctl start wiki-worker@4
```

### 3. Check status

```bash
# Check all workers
sudo systemctl status wiki-worker@*

# View logs
sudo journalctl -u wiki-worker@1 -f

# Or check log files
tail -f /var/log/wiki-worker-1.log
```

### 4. Manage workers

```bash
# Restart a worker
sudo systemctl restart wiki-worker@1

# Stop a worker
sudo systemctl stop wiki-worker@1

# Stop all workers
sudo systemctl stop wiki-worker@{1..4}
```

## Configuration

Edit `/etc/systemd/system/wiki-worker@.service` to adjust:

- `User`: User to run worker as
- `WorkingDirectory`: Path to application
- `Environment`: Flask environment variables
- `ExecStart`: Path to worker script

## Monitoring

```bash
# View worker status
sudo systemctl status wiki-worker@*

# Check worker processes
ps aux | grep worker.py

# Monitor logs in real-time
sudo journalctl -u wiki-worker@1 -u wiki-worker@2 -u wiki-worker@3 -u wiki-worker@4 -f
```
