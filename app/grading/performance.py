import asyncpg
import time
import os

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://grader:password@localhost/test_grader")

async def check_performance(sql_query: str) -> float:
    try:
        conn = await asyncpg.connect(TEST_DB_URL)
        start = time.time()
        if sql_query.strip().upper().startswith("SELECT"):
            await conn.fetch(sql_query)
        else:
            await conn.execute(sql_query)
        end = time.time()
        await conn.close()
        return end - start
    except:
        return float('inf')