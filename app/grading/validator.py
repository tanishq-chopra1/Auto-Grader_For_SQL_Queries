import asyncpg
import os

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://grader:password@localhost/test_grader")

async def validate_query(sql_query: str) -> tuple[bool, str]:
    try:
        conn = await asyncpg.connect(TEST_DB_URL)
        # For SELECT queries, execute and check if no error
        if sql_query.strip().upper().startswith("SELECT"):
            result = await conn.fetch(sql_query)
            await conn.close()
            return True, f"Returned {len(result)} rows"
        else:
            # For other queries, execute
            await conn.execute(sql_query)
            await conn.close()
            return True, "Query executed successfully"
    except Exception as e:
        return False, str(e)

async def analyze_query_plan(sql_query: str) -> str:
    try:
        conn = await asyncpg.connect(TEST_DB_URL)
        explain_query = f"EXPLAIN {sql_query}"
        result = await conn.fetch(explain_query)
        plan = "\n".join([row[0] for row in result])
        await conn.close()
        return plan
    except Exception as e:
        return f"Error analyzing plan: {str(e)}"