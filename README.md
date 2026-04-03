# Auto-Grader for SQL Queries

An intelligent system that automatically grades SQL queries from submission files using asynchronous processing, AI-powered feedback, and performance analysis with human-in-the-loop.

## Setup Instructions

### 1. Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ (if running locally)
- Google Gemini API Key

### 2. Get Your Gemini API Key

1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key (starts with `AIza...`)

### 3. Configure the Application

1. Create a `.env` file in the project root:
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

2. Ensure `rubric.txt` exists with your grading rubric:
   ```
   Define your SQL grading criteria here
   Points for: correctness, optimization, efficiency
   ```

3. Create `submissions/` folder (auto-created on first run):
   ```bash
   mkdir -p submissions reports
   ```

### 4. Start the Application

```bash
docker-compose up --build
```

This starts all services:
- FastAPI app on http://localhost:8000
- PostgreSQL database on port 5432
- MongoDB on port 27017
- Redis on port 6379

Check the console for "Application startup complete" message.

## How to Use

### Adding Submissions

1. **Place files in the `submissions/` folder:**
   - `.txt` - Plain SQL queries
   - `.pdf` - Scanned or digital documents with SQL
   - `.docx` - Word documents with SQL queries

2. **File naming convention:**
   - `1_query.txt` → Assignment ID: 1
   - `SQL Queries Quiz 7.pdf` → Assignment ID: SQL
   - Any file format is supported (PDF, DOCX, TXT)

### Automatic Processing

The system automatically:
- ✓ Detects new files in the submission folder
- ✓ Extracts all SQL queries from documents
- ✓ Creates submission records
- ✓ Grades each query asynchronously
- ✓ Generates final Excel report

### Viewing Results

1. Check **console logs** for grading progress
2. Open **`reports/final_report.xlsx`** for complete results:
   - Student ID
   - Assignment ID
   - Query text
   - Grading status
   - Score (0-100)
   - Execution time
   - AI-generated feedback

### Example Workflow

```bash
# 1. Place files
cp my_queries.pdf submissions/

# 2. Start grading
docker-compose up

# 3. Wait for completion (check logs)
# ✓ Processing 1_query.txt
# ✓ Found 1 queries in 1_query.txt
# ✓ Final report saved to reports/final_report.xlsx

# 4. Check results
open reports/final_report.xlsx
```

## Features

- 📁 **Batch Processing**: Process multiple files at once
- 🔍 **Multi-Format Support**: PDF, DOCX, and TXT extraction
- ⚡ **Async Grading**: Non-blocking processing for fast results
- 🧪 **Query Execution**: Tests queries against test database
- 📊 **Performance Analysis**: Execution time and result metrics
- 🔎 **Plan Analysis**: Explain output inspection for optimization
- 🤖 **AI Feedback**: Gemini-powered suggestions and improvements
- 📈 **Vector Search**: FAISS similarity matching for context
- 📋 **Excel Reports**: Final grades in spreadsheet format
- 🔒 **Hybrid Storage**: PostgreSQL + MongoDB for reliability
- 🛡️ **Error Handling**: Graceful failures with detailed logs

## Tech Stack

### Backend & Processing
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - ORM for database operations

### Databases
- **PostgreSQL 15** - Relational database for submissions & grades
- **MongoDB 7** - NoSQL for FAISS embeddings
- **Redis 7** - In-memory caching

### AI & Machine Learning
- **SentenceTransformers** - Query embedding generation
- **FAISS** - Vector similarity search
- **Google Gemini API** - LLM feedback generation
- **NumPy** - Numerical computing

### File Processing
- **PyPDF2** - PDF text extraction
- **python-docx** - DOCX document parsing
- **openpyxl** - Excel report generation

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **asyncpg** - Async PostgreSQL driver
- **Celery** - Async task queue

## Troubleshooting

### Extension doesn't start
- Make sure Docker is running: `docker ps`
- Check for port conflicts: `netstat -an | grep 8000`
- Verify all images downloaded: `docker images`

### "No submission files found"
- Check that files are in `submissions/` folder
- Verify file extensions are `.txt`, `.pdf`, or `.docx`
- Check file permissions (readable by Docker)

### "No SQL queries found in {filename}"
- Your file doesn't contain valid SQL
- Check text extraction worked properly
- For PDFs: scanned images won't extract text (use OCR first)

### ⏳ Stuck on "Generating..."
- Check API key is correct (starts with `AIza...`)
- Verify Gemini API is enabled: https://aistudio.google.com/app/apikey
- Check Docker logs: `docker-compose logs app`

### Report not generated
- Wait for "Final report saved to reports/final_report.xlsx" message
- Check `reports/` folder exists
- Verify file permissions for write access

### Database connection errors
- Make sure all containers are running: `docker-compose ps`
- Check environment variables in docker-compose.yml
- Clear volumes and restart: `docker-compose down -v && docker-compose up`

## Environment Variables

```bash
# Google Gemini API
GOOGLE_API_KEY=your_key_here

# Database connections (auto-configured in Docker)
DATABASE_URL=postgresql+asyncpg://grader:password@db/grader
TEST_DATABASE_URL=postgresql+asyncpg://grader:password@test_db/test_grader
MONGO_URL=mongodb://mongo:27017
REDIS_URL=redis://redis:6379/0
```

## Technical Details

- **API**: Google Gemini 2.0 Flash
- **Database**: PostgreSQL 15 + MongoDB 7
- **Python Version**: 3.11
- **Async Framework**: FastAPI with asyncio
- **Vector Database**: FAISS with MongoDB storage
- **Docker Compose**: Multi-service orchestration

## Project Structure

```
Auto-Grader Project/
├── app/
│   ├── main.py                 # Entry point, file processor
│   ├── models.py              # SQLAlchemy models
│   ├── database.py            # DB configuration
│   └── grading/
│       ├── tasks.py           # Grading pipeline
│       └── file_processor.py  # PDF/DOCX/TXT extraction
├── submissions/               # Input folder for submission files
├── reports/                   # Output folder for Excel reports
├── rubric.txt                 # Grading criteria
├── docker-compose.yml         # Service configuration
├── Dockerfile                 # App container definition
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Privacy & Security

- 🔒 API keys stored locally in environment variables
- 📨 Messages sent directly to Google's Gemini API
- 🚫 No data stored on third-party servers
- 📁 Local file processing on your machine
- 🛡️ Submissions only accessible to Docker services

---

## Quick Checklist

Make sure you've completed these steps before running:

- ✅ Set `GOOGLE_API_KEY` in `.env` file
- ✅ Created `submissions/` folder
- ✅ Created `rubric.txt` with grading criteria
- ✅ Docker and Docker Compose installed
- ✅ Placed submission files in `submissions/` folder
- ✅ Run `docker-compose up --build`
- ✅ Check logs for "Application startup complete"
- ✅ Wait for "Final report saved to reports/final_report.xlsx"
- ✅ Open the Excel file to view results

 
