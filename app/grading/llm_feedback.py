import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

async def generate_feedback(sql_query: str, is_valid: bool, validation_msg: str, exec_time: float, query_plan: str, similar_queries: list) -> str:
    prompt = f"""
    Analyze the following SQL query submission and provide constructive feedback for a student.

    Query: {sql_query}

    Validation: {'Passed' if is_valid else 'Failed'} - {validation_msg}

    Execution Time: {exec_time:.2f} seconds

    Query Plan: {query_plan}

    Similar Queries: {', '.join(similar_queries) if similar_queries else 'None'}

    Provide detailed feedback on correctness, performance, and suggestions for improvement.
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating feedback: {str(e)}"