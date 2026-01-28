
import psycopg2
import sys

USER = "postgres.vbjbywbuiwnqjdftbdfb"
PASS = "J8cNPmXI6SMdlwwS"
HOST = "aws-0-ap-south-1.pooler.supabase.com"
PORT = 5432
DB = "postgres"

print(f"Connecting to {HOST} as {USER}...")

try:
    conn = psycopg2.connect(
        host=HOST,
        user=USER,
        password=PASS,
        dbname=DB,
        port=PORT,
        connect_timeout=10
    )
    print("✅ SUCCESS! Connection established.")
    conn.close()
except Exception as e:
    print(f"❌ FAILED: {e}")
