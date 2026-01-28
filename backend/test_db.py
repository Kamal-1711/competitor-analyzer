import asyncio
import asyncpg
import sys

async def test_connection():
    # Try Pooler
    url = "postgresql://postgres.xsnwyuqrltkrcafmlojz:0r2E8wbJn3qjNsEZ@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    print(f"Testing Pooler connection: {url}")
    try:
        conn = await asyncpg.connect(url)
        print("Successfully connected to Pooler!")
        await conn.close()
    except Exception as e:
        print(f"Pooler connection failed: {type(e).__name__}: {e}")

    # Try Direct
    url_direct = "postgresql://postgres:0r2E8wbJn3qjNsEZ@db.xsnwyuqrltkrcafmlojz.supabase.co:5432/postgres"
    print(f"\nTesting Direct connection: {url_direct}")
    try:
        conn = await asyncpg.connect(url_direct)
        print("Successfully connected to Direct!")
        await conn.close()
    except Exception as e:
        print(f"Direct connection failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
