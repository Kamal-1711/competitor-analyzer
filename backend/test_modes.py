import psycopg2

configs = [
    {"name": "Session Mode (5432)", "port": 5432, "host": "aws-0-ap-south-1.pooler.supabase.com", "user": "postgres.vbjbywbuiwnqjdftbdfb"},
    {"name": "Transaction Mode (6543)", "port": 6543, "host": "aws-0-ap-south-1.pooler.supabase.com", "user": "postgres.vbjbywbuiwnqjdftbdfb"},
]

password = "J8cNPmXI6SMdlwwS"

for cfg in configs:
    print(f'Testing {cfg["name"]}...')
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname="postgres",
            user=cfg["user"],
            password=password,
            connect_timeout=10
        )
        print("  SUCCESS!")
        conn.close()
    except Exception as e:
        err = str(e).split("\n")[0][:80]
        print(f"  FAILED: {err}")
