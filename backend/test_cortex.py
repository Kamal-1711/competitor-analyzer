import asyncio
import asyncpg

async def test_connection():
    # Try Cortex project with same password
    url = "postgresql://postgres.hvnxvmisfwtmrrxqblxq:0r2E8wbJn3qjNsEZ@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    print(f"Testing Cortex Pooler connection: {url}")
    try:
        conn = await asyncpg.connect(url)
        print("Successfully connected to Cortex Pooler!")
        await conn.close()
    except Exception as e:
        print(f"Cortex connection failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
