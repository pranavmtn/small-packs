"""Quick DB connectivity check."""

from dotenv import load_dotenv

load_dotenv(override=True)

from sqlalchemy import create_engine, text

from config import Config

print("configured:", Config.DATABASE_CONFIGURED)
print("using pooler:", "pooler.supabase.com" in Config.SQLALCHEMY_DATABASE_URI)
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
with engine.connect() as conn:
    n = conn.execute(text("select count(*) from inventory_items")).scalar()
    print("connected OK")
    print("inventory_items rows:", n)
