# Docker Compose Guide

Docker Compose is a tool for defining and running multi-container Docker applications. With Compose, you use a YAML file to configure your application's services.

## Basic Concepts

### Services
A service is a container running an image. Services can be scaled to run multiple containers.

### Networks
By default, Compose sets up a single network for your app. Each container can communicate with others using the service name as hostname.

### Volumes
Persist data generated and used by Docker containers.

## Installation

Docker Compose comes bundled with Docker Desktop. For Linux:

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## docker-compose.yml Structure

Basic structure:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/code
    environment:
      FLASK_ENV: development
  
  redis:
    image: "redis:alpine"
```

## Common Commands

### Start services
```bash
docker-compose up
docker-compose up -d  # Detached mode
```

### Stop services
```bash
docker-compose down
docker-compose down -v  # Remove volumes too
```

### View logs
```bash
docker-compose logs
docker-compose logs -f web  # Follow specific service
```

### Execute commands
```bash
docker-compose exec web python manage.py migrate
```

### Rebuild services
```bash
docker-compose build
docker-compose up --build  # Build and start
```

## Real-World Example

Complete stack for a web application:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  web:
    build: .
    command: python app.py
    volumes:
      - .:/app
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/myapp
      REDIS_URL: redis://redis:6379/0
  
  worker:
    build: .
    command: python worker.py
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/myapp
      REDIS_URL: redis://redis:6379/0

volumes:
  postgres_data:
```

## Environment Variables

### Using .env file
```env
POSTGRES_PASSWORD=supersecret
API_KEY=abc123
```

Reference in compose file:
```yaml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

### env_file directive
```yaml
services:
  web:
    env_file:
      - .env
      - .env.local
```

## Health Checks

Define health checks for services:

```yaml
services:
  web:
    image: nginx
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Scaling Services

```bash
docker-compose up -d --scale worker=3
```

## Best Practices

1. Use specific image versions, not `latest`
2. Leverage build cache with proper layer ordering
3. Use named volumes for persistent data
4. Set resource limits for production
5. Use secrets for sensitive data
6. Implement health checks
7. Use multi-stage builds to reduce image size

## Troubleshooting

### View service status
```bash
docker-compose ps
```

### Inspect networks
```bash
docker network ls
docker network inspect myapp_default
```

### Remove everything
```bash
docker-compose down --rmi all --volumes --remove-orphans
```
