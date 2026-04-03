from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class GradingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    assignment_id = Column(String, index=True)
    sql_query = Column(Text, nullable=False)
    status = Column(Enum(GradingStatus), default=GradingStatus.PENDING)
    score = Column(Float, nullable=True)
    execution_time = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    reviews = relationship("Review", back_populates="submission")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    reviewer_id = Column(String, index=True)
    score_override = Column(Float, nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default="now()")

    submission = relationship("Submission", back_populates="reviews")