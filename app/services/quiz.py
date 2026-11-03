from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import QuestionKind, QuizAnswer, QuizQuestion
from app.schemas.quiz import AnswerIn, AnswerResult, OptionPublic, QuestionPublic

QUESTION_LOAD_OPTIONS = selectinload(QuizQuestion.options)


def normalize_text(text: str) -> str:
    return " ".join(text.split()).casefold()


def unprocessable(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail)


def grade(question: QuizQuestion, answer: AnswerIn) -> tuple[bool, dict[str, Any]]:
    if question.kind == QuestionKind.TEXT:
        if not answer.text or not answer.text.strip():
            raise unprocessable("Введите ответ")
        given = normalize_text(answer.text)
        is_correct = any(normalize_text(option.text) == given for option in question.options)
        return is_correct, {"text": answer.text.strip()}

    selected = set(answer.option_ids)
    if not selected:
        raise unprocessable("Выберите вариант ответа")
    if not selected <= {option.id for option in question.options}:
        raise unprocessable("Такого варианта нет в этом вопросе")
    if question.kind == QuestionKind.SINGLE and len(selected) != 1:
        raise unprocessable("В этом вопросе можно выбрать только один вариант")
    correct = {option.id for option in question.options if option.is_correct}
    return selected == correct, {"option_ids": sorted(selected)}


def to_result(question: QuizQuestion, answer: QuizAnswer) -> AnswerResult:
    is_text = question.kind == QuestionKind.TEXT
    return AnswerResult(
        question_id=question.id,
        is_correct=answer.is_correct,
        option_ids=answer.answer.get("option_ids", []),
        text=answer.answer.get("text"),
        correct_option_ids=[] if is_text else [o.id for o in question.options if o.is_correct],
        accepted_answers=[o.text for o in question.options] if is_text else [],
        explanation=question.explanation,
        answered_at=answer.answered_at,
    )


def to_public(question: QuizQuestion, answer: QuizAnswer | None) -> QuestionPublic:
    options = (
        []
        if question.kind == QuestionKind.TEXT
        else [OptionPublic(id=option.id, text=option.text) for option in question.options]
    )
    return QuestionPublic(
        id=question.id,
        position=question.position,
        kind=question.kind,
        prompt=question.prompt,
        options=options,
        result=to_result(question, answer) if answer is not None else None,
    )


async def load_lesson_questions(session: AsyncSession, lesson_id: int) -> list[QuizQuestion]:
    questions = await session.scalars(
        select(QuizQuestion)
        .where(QuizQuestion.lesson_id == lesson_id)
        .options(QUESTION_LOAD_OPTIONS)
        .order_by(QuizQuestion.position, QuizQuestion.id)
    )
    return list(questions)


async def count_questions(session: AsyncSession, lesson_ids: list[int]) -> dict[int, int]:
    if not lesson_ids:
        return {}
    rows = await session.execute(
        select(QuizQuestion.lesson_id, func.count(QuizQuestion.id))
        .where(QuizQuestion.lesson_id.in_(lesson_ids))
        .group_by(QuizQuestion.lesson_id)
    )
    return {lesson_id: count for lesson_id, count in rows}
