from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, false
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import QuestionKind, db_enum


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]
    kind: Mapped[QuestionKind] = mapped_column(db_enum(QuestionKind, "question_kind"))
    prompt: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text, default="", server_default="")

    options: Mapped[list["QuizOption"]] = relationship(
        back_populates="question",
        order_by="QuizOption.position, QuizOption.id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class QuizOption(Base):
    __tablename__ = "quiz_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]
    text: Mapped[str] = mapped_column(String(500))
    is_correct: Mapped[bool] = mapped_column(default=False, server_default=false())

    question: Mapped[QuizQuestion] = relationship(back_populates="options", lazy="raise")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    __table_args__ = (UniqueConstraint("user_id", "question_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"), index=True
    )
    is_correct: Mapped[bool]
    answer: Mapped[dict[str, Any]] = mapped_column(JSONB)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
