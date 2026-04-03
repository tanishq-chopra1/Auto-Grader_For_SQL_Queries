import re
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_file = BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(BytesIO(file_bytes))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode('utf-8')

def extract_sql_queries(text: str) -> list[str]:
    # Simple regex to find SQL-like statements
    # This is basic; in practice, might need better parsing
    sql_pattern = re.compile(r'(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s+.*?;', re.IGNORECASE | re.DOTALL)
    queries = sql_pattern.findall(text)
    return queries