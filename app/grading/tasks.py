import asyncio
import time
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models import Submission, GradingStatus
from app.grading.validator import validate_query, analyze_query_plan
from app.grading.performance import check_performance
from app.grading.faiss_handler import find_similar_queries
from app.grading.llm_feedback import generate_feedback
from app.grading.rubric_loader import load_rubric, calculate_score, generate_feedback as rubric_feedback

async def grade_submission(submission_id: int):
    async with async_session() as db:
        submission = await db.get(Submission, submission_id)
        if not submission:
            return
        
        submission.status = GradingStatus.PROCESSING
        submission.updated_at = datetime.datetime.utcnow()
        await db.commit()
        
        try:
            # Execution validation
            is_valid, validation_feedback = await validate_query(submission.sql_query)
            
            # Performance check
            exec_time = await check_performance(submission.sql_query)
            
            # Query plan analysis
            query_plan = await analyze_query_plan(submission.sql_query)
            
            # FAISS similarity
            similar_queries = await find_similar_queries(submission.sql_query)
            
            # Load rubric
            rubric = load_rubric("rubric.txt")
            
            # Calculate score based on rubric
            score = calculate_score(is_valid, exec_time, query_plan, rubric)
            
            # Generate feedback (combine rubric and LLM)
            rubric_fb = rubric_feedback(is_valid, exec_time, query_plan, rubric)
            llm_fb = await generate_feedback(
                submission.sql_query, is_valid, validation_feedback, exec_time, query_plan, similar_queries
            )
            feedback = f"{rubric_fb}\n\n{llm_fb}"
            
            submission.score = score
            submission.execution_time = exec_time
            submission.feedback = feedback
            submission.status = GradingStatus.COMPLETED
            submission.updated_at = datetime.datetime.utcnow()
            
        except Exception as e:
            submission.status = GradingStatus.FAILED
            submission.feedback = str(e)
            submission.updated_at = datetime.datetime.utcnow()
        
        await db.commit()