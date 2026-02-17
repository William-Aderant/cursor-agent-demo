#!/bin/bash
# Database helper script for cursor-agent-demo
# Provides convenient commands for managing the local PostgreSQL database

# Add PostgreSQL to PATH
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

DB_NAME="cursor_agent_demo"
DB_USER="${USER:-william.holden}"
DB_URL="postgresql://${DB_USER}@localhost:5432/${DB_NAME}"

case "$1" in
  start)
    echo "Starting PostgreSQL..."
    brew services start postgresql@15
    ;;
  stop)
    echo "Stopping PostgreSQL..."
    brew services stop postgresql@15
    ;;
  status)
    echo "PostgreSQL service status:"
    brew services list | grep postgresql@15
    ;;
  connect)
    echo "Connecting to database: ${DB_NAME}"
    psql -d "${DB_NAME}"
    ;;
  reset)
    echo "⚠️  WARNING: This will drop and recreate the database!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      dropdb "${DB_NAME}" 2>/dev/null || true
      createdb "${DB_NAME}"
      echo "✅ Database ${DB_NAME} has been reset"
    fi
    ;;
  url)
    echo "${DB_URL}"
    ;;
  *)
    echo "Usage: $0 {start|stop|status|connect|reset|url}"
    echo ""
    echo "Commands:"
    echo "  start    - Start PostgreSQL service"
    echo "  stop     - Stop PostgreSQL service"
    echo "  status   - Show PostgreSQL service status"
    echo "  connect  - Connect to the database with psql"
    echo "  reset    - Drop and recreate the database (⚠️  destructive)"
    echo "  url      - Print the connection string"
    exit 1
    ;;
esac
