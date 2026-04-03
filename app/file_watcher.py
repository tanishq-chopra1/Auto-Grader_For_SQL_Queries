import os
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.grading.file_processor import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt, extract_sql_queries
from app.grading.tasks import grade_submission
from app.database import async_session
from app.models import Submission
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SubmissionHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.pdf', '.docx', '.txt')):
            logger.info(f"New submission file: {event.src_path}")
            asyncio.run_coroutine_threadsafe(self.process_file(event.src_path), self.loop)

    async def process_file(self, file_path):
        # Parse filename: optionally {student_id}_{assignment_id}_{filename} or {assignment_id}_{filename}
        filename = os.path.basename(file_path)
        parts = filename.split('_', 2)
        if len(parts) == 2:
            # No student_id: assignment_id_filename
            student_id = "anonymous"
            assignment_id = parts[0]
        elif len(parts) >= 3:
            # With student_id: student_id_assignment_id_filename
            student_id = parts[0]
            assignment_id = parts[1]
        else:
            logger.error(f"Invalid filename format: {filename}")
            return

        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()

            if filename.endswith('.pdf'):
                text = extract_text_from_pdf(file_bytes)
            elif filename.endswith('.docx'):
                text = extract_text_from_docx(file_bytes)
            elif filename.endswith('.txt'):
                text = extract_text_from_txt(file_bytes)
            else:
                return

            queries = extract_sql_queries(text)
            if not queries:
                logger.warning(f"No SQL queries found in {filename}")
                return

            async with async_session() as db:
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
                    asyncio.create_task(grade_submission(sub_id))
                
                logger.info(f"Processed {len(queries)} queries from {filename}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

def start_file_watcher(loop):
    event_handler = SubmissionHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, path='submissions', recursive=False)
    observer.start()
    logger.info("File watcher started for submissions folder")
    return observer