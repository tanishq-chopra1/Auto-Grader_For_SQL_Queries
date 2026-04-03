from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Submission, GradingStatus
from app.grading.tasks import grade_submission
from app.grading.file_processor import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt, extract_sql_queries
from pydantic import BaseModel
import openpyxl
import os

router = APIRouter()

class SubmitQueryRequest(BaseModel):
    student_id: str
    assignment_id: str
    sql_query: str

class SubmissionResponse(BaseModel):
    id: int
    status: GradingStatus
    score: float = None
    feedback: str = None

@router.post("/submit", response_model=SubmissionResponse)
async def submit_query(request: SubmitQueryRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    submission = Submission(
        student_id=request.student_id,
        assignment_id=request.assignment_id,
        sql_query=request.sql_query
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    
    background_tasks.add_task(grade_submission, submission.id)
    
    return SubmissionResponse(
        id=submission.id,
        status=submission.status,
        score=submission.score,
        feedback=submission.feedback
    )

@router.post("/submit-file")
async def submit_file(
    student_id: str,
    assignment_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT files are supported")
    
    file_bytes = await file.read()
    
    # Save file to submissions folder
    import os
    submissions_dir = "submissions"
    os.makedirs(submissions_dir, exist_ok=True)
    file_path = os.path.join(submissions_dir, f"{student_id}_{assignment_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    elif file.filename.endswith(".txt"):
        text = extract_text_from_txt(file_bytes)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    queries = extract_sql_queries(text)
    if not queries:
        raise HTTPException(status_code=400, detail="No SQL queries found in the file")
    
    submission_ids = []
    for query in queries:
        submission = Submission(
            student_id=student_id,
            assignment_id=assignment_id,
            sql_query=query.strip()
        )
        db.add(submission)
        submission_ids.append(submission.id)
    
    await db.commit()
    
    for sub_id in submission_ids:
        background_tasks.add_task(grade_submission, sub_id)
    
    return {"message": f"Extracted and submitted {len(queries)} queries", "submission_ids": submission_ids, "file_saved": file_path}

@router.get("/submission/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: int, db: AsyncSession = Depends(get_db)):
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return SubmissionResponse(
        id=submission.id,
        status=submission.status,
        score=submission.score,
        feedback=submission.feedback
    )

# Human review endpoint
@router.post("/review/{submission_id}")
async def review_submission(submission_id: int, score: float, comments: str, reviewer_id: str, db: AsyncSession = Depends(get_db)):
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    from app.models import Review
    review = Review(
        submission_id=submission_id,
        reviewer_id=reviewer_id,
        score_override=score,
        comments=comments
    )
    db.add(review)
    submission.status = GradingStatus.REVIEWED
    submission.score = score
    await db.commit()
    
    return {"message": "Review submitted"}

@router.get("/report/{assignment_id}")
async def generate_report(assignment_id: str, db: AsyncSession = Depends(get_db)):
    # Query all submissions for the assignment
    result = await db.execute(select(Submission).where(Submission.assignment_id == assignment_id))
    submissions = result.scalars().all()
    
    if not submissions:
        raise HTTPException(status_code=404, detail="No submissions found for this assignment")
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Grades and Feedback"
    
    # Headers
    ws.append(["Student ID", "Query", "Status", "Score", "Execution Time", "Feedback"])
    
    # Data
    for sub in submissions:
        ws.append([
            sub.student_id,
            sub.sql_query,
            sub.status.value,
            sub.score,
            sub.execution_time,
            sub.feedback
        ])
    
    # Save to file
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, f"report_{assignment_id}.xlsx")
    wb.save(file_path)
    
    return FileResponse(file_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=f"grades_{assignment_id}.xlsx")