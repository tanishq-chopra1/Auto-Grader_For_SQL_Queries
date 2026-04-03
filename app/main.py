from fastapi import FastAPI
from app.database import create_tables, async_session
from app.models import Submission
from app.grading.file_processor import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt, extract_sql_queries
from app.grading.tasks import grade_submission
import openpyxl
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SQL Grader", version="1.0.0")

SUBMISSIONS_DIR = "submissions"
REPORTS_DIR = "reports"

async def process_all_submissions():
    """Process all files in the submissions folder."""
    if not os.path.exists(SUBMISSIONS_DIR):
        logger.info(f"Submissions directory {SUBMISSIONS_DIR} does not exist. Skipping processing.")
        return

    files = [f for f in os.listdir(SUBMISSIONS_DIR) if f.endswith(('.pdf', '.docx', '.txt'))]
    if not files:
        logger.info("No submission files found.")
        return

    logger.info(f"Processing {len(files)} submission files...")

    async with async_session() as db:
        for filename in files:
            file_path = os.path.join(SUBMISSIONS_DIR, filename)
            logger.info(f"Processing {filename}")

            # Parse filename to extract assignment_id
            # Remove extension
            if filename.endswith('.pdf'):
                basename = filename[:-4]
                file_type = 'pdf'
            elif filename.endswith('.docx'):
                basename = filename[:-5]
                file_type = 'docx'
            elif filename.endswith('.txt'):
                basename = filename[:-4]
                file_type = 'txt'
            else:
                logger.warning(f"Unknown file type: {filename}")
                continue
            
            # Extract assignment_id from filename (e.g., "1_query" or "SQL Queries Quiz 7")
            # First part or first number found
            parts = basename.split('_')
            if parts:
                # Try to use first part as assignment_id
                try:
                    assignment_id = parts[0]
                except:
                    assignment_id = basename
            else:
                assignment_id = basename
            
            student_id = "anonymous"

            try:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()

                if file_type == 'pdf':
                    text = extract_text_from_pdf(file_bytes)
                elif file_type == 'docx':
                    text = extract_text_from_docx(file_bytes)
                elif file_type == 'txt':
                    text = extract_text_from_txt(file_bytes)
                else:
                    continue

                queries = extract_sql_queries(text)
                if not queries:
                    logger.warning(f"No SQL queries found in {filename}")
                    continue

                logger.info(f"Found {len(queries)} queries in {filename}")
                for query in queries:
                    submission = Submission(
                        student_id=student_id,
                        assignment_id=assignment_id,
                        sql_query=query.strip()
                    )
                    db.add(submission)
                    await db.commit()
                    await db.refresh(submission)
                    logger.info(f"Created submission {submission.id} from {filename}")
                    await grade_submission(submission.id)

            except Exception as e:
                logger.error(f"Error processing {filename}: {e}", exc_info=True)

    logger.info("All submissions processed.")

async def generate_final_report():
    """Generate a final Excel report for all submissions."""
    async with async_session() as db:
        from sqlalchemy import select
        result = await db.execute(select(Submission))
        submissions = result.scalars().all()

    if not submissions:
        logger.info("No submissions to report.")
        return

    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Final Grades and Feedback"

    # Headers
    ws.append(["Student ID", "Assignment ID", "Query", "Status", "Score", "Execution Time", "Feedback"])

    # Data
    for sub in submissions:
        ws.append([
            sub.student_id,
            sub.assignment_id,
            sub.sql_query,
            sub.status.value if sub.status else "UNKNOWN",
            sub.score,
            sub.execution_time,
            sub.feedback
        ])

    # Save to file
    os.makedirs(REPORTS_DIR, exist_ok=True)
    file_path = os.path.join(REPORTS_DIR, "final_report.xlsx")
    wb.save(file_path)
    logger.info(f"Final report saved to {file_path}")

@app.on_event("startup")
async def startup_event():
    await create_tables()
    await process_all_submissions()
    await generate_final_report()
    logger.info("Batch processing complete. Check the reports folder for final_report.xlsx")

@app.get("/")
async def root():
    return {"message": "SQL Grader - Batch processing complete. Check reports/final_report.xlsx"}