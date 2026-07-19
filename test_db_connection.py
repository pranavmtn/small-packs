#!/usr/bin/env python3
"""Test Supabase database connection."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
env_path = Path(__file__).resolve().parent / ".env"
if os.getenv("FLASK_ENV", "development") == "development":
    load_dotenv(env_path, override=True)
    print(f"✓ Loaded .env from {env_path}")
else:
    print(f"⊘ Skipping .env (FLASK_ENV={os.getenv('FLASK_ENV')})")

# Check environment variables
print("\n=== Environment Variables ===")
supabase_db_url = os.getenv("SUPABASE_DB_URL", "").strip()
supabase_url = os.getenv("SUPABASE_URL", "").strip()
supabase_key = os.getenv("SUPABASE_KEY", "").strip()

print(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'NOT SET')}")
print(f"SUPABASE_DB_URL: {'SET' if supabase_db_url else 'NOT SET'}")
if supabase_db_url:
    # Hide password in output
    safe_url = supabase_db_url.split("@")[0] + "@[HIDDEN]"
    print(f"  → {safe_url}")
print(f"SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
print(f"SUPABASE_KEY: {'SET' if supabase_key else 'NOT SET'}")

# Import and use config
print("\n=== Loading Config ===")
from config import Config

print(f"DATABASE_CONFIGURED: {Config.DATABASE_CONFIGURED}")
print(f"SQLALCHEMY_DATABASE_URI: {Config.SQLALCHEMY_DATABASE_URI[:50]}...")

# Test connection
print("\n=== Testing Database Connection ===")
if not Config.DATABASE_CONFIGURED:
    print("✗ ERROR: Database is not configured")
    print("  Make sure SUPABASE_DB_URL is set correctly")
    sys.exit(1)

try:
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1 as connection_test"))
        value = result.scalar()
        print(f"✓ Database connection successful!")
        print(f"  Query result: {value}")
except Exception as e:
    print(f"✗ Database connection failed!")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error message: {str(e)}")
    
    # Try to provide helpful hints
    if "could not resolve hostname" in str(e).lower():
        print("\n  💡 Hint: DNS resolution failed. Check the host in your connection string.")
    elif "connection refused" in str(e).lower():
        print("\n  💡 Hint: Connection refused. Check if Supabase is running and accessible.")
    elif "password authentication failed" in str(e).lower():
        print("\n  💡 Hint: Authentication failed. Check your password in SUPABASE_DB_URL.")
    elif "no route to host" in str(e).lower():
        print("\n  💡 Hint: Network unreachable. Your IP may be blocked by Supabase firewall.")
    
    sys.exit(1)

print("\n✓ All checks passed!")
