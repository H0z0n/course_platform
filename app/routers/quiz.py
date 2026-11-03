from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, OptionalUser, SessionDep, StaffUser
from app.models import Lesson, QuizAnswer, QuizOption, QuizQuestion, User
from app.schemas.common import ReorderRequest
from app.schemas.quiz import AnswerIn, AnswerResult, QuestionAdmin, QuestionIn, QuestionPublic
from app.services.access import ensure_can_open, get_course_access, get_lesson_with_course_id
from app.services.common import get_or_404
from app.services.ordering import apply_order, next_position
from app.services.quiz import (
    QUESTION_LOAD_OPTIONS,
    grade,
    load_lesson_questions,
    to_public,
    to_result,
)

router = APIRouter(tags=["quiz"])


async def ensure_lesson_open(session: AsyncSession, lesson_id: int, user: User | None) -> None:
    lesson, course_id = await get_lesson_with_course_id(session, lesson_id)
    access = await get_course_access(session, user, course_id)
    ensure_can_open(access, lesson, user)


async def get_question_or_404(session: AsyncSession, question_id: int) -> QuizQuestion:
    question = await session.scalar(
        select(QuizQuestion).where(QuizQuestion.id == question_id).options(QUESTION_LOAD_OPTIONS)
    )
    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Вопрос не найден")
    return question


def build_options(payload: QuestionIn) -> list[QuizOption]:
    return [
        QuizOption(position=position, text=option.text, is_correct=option.is_correct)
        for position, option in enumerate(payload.options, start=1)
    ]


@router.get("/lessons/{lesson_id}/questions", response_model=list[QuestionPublic])
async def list_questions(lesson_id: int, session: SessionDep, user: OptionalUser):
    await ensure_lesson_open(session, lesson_id, user)
    questions = await load_lesson_questions(session, lesson_id)
    answers: dict[int, QuizAnswer] = {}
    if user is not None and questions:
        rows = await session.scalars(
            select(QuizAnswer).where(
                QuizAnswer.user_id == user.id,
                QuizAnswer.question_id.in_([question.id for question in questions]),
            )
        )
        answers = {answer.question_id: answer for answer in rows}
    return [to_public(question, answers.get(question.id)) for question in questions]


@router.post("/questions/{question_id}/answer", response_model=AnswerResult)
async def answer_question(
    question_id: int, payload: AnswerIn, session: SessionDep, user: CurrentUser
):
    question = await get_question_or_404(session, question_id)
    await ensure_lesson_open(session, question.lesson_id, user)
    is_correct, answer_data = grade(question, payload)

    answer = await session.scalar(
        select(QuizAnswer).where(
            QuizAnswer.user_id == user.id, QuizAnswer.question_id == question_id
        )
    )
    if answer is None:
        answer = QuizAnswer(user_id=user.id, question_id=question_id)
        session.add(answer)
    answer.is_correct = is_correct
    answer.answer = answer_data
    answer.answered_at = datetime.now(UTC)
    await session.commit()
    return to_result(question, answer)


@router.get("/lessons/{lesson_id}/questions/manage", response_model=list[QuestionAdmin])
async def list_questions_for_staff(lesson_id: int, session: SessionDep, _: StaffUser):
    await get_or_404(session, Lesson, lesson_id, "Урок не найден")
    return await load_lesson_questions(session, lesson_id)


@router.post(
    "/lessons/{lesson_id}/questions",
    response_model=QuestionAdmin,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    lesson_id: int, payload: QuestionIn, session: SessionDep, _: StaffUser
):
    await get_or_404(session, Lesson, lesson_id, "Урок не найден")
    question = QuizQuestion(
        lesson_id=lesson_id,
        position=await next_position(
            session, QuizQuestion.position, QuizQuestion.lesson_id == lesson_id
        ),
        kind=payload.kind,
        prompt=payload.prompt,
        explanation=payload.explanation,
        options=build_options(payload),
    )
    session.add(question)
    await session.commit()
    return question


@router.put("/questions/{question_id}", response_model=QuestionAdmin)
async def replace_question(
    question_id: int, payload: QuestionIn, session: SessionDep, _: StaffUser
):
    question = await get_question_or_404(session, question_id)
    question.kind = payload.kind
    question.prompt = payload.prompt
    question.explanation = payload.explanation
    question.options = build_options(payload)
    await session.execute(delete(QuizAnswer).where(QuizAnswer.question_id == question_id))
    await session.commit()
    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, session: SessionDep, _: StaffUser):
    question = await get_or_404(session, QuizQuestion, question_id, "Вопрос не найден")
    await session.delete(question)
    await session.commit()


@router.put("/lessons/{lesson_id}/questions/order", response_model=list[QuestionAdmin])
async def reorder_questions(
    lesson_id: int, payload: ReorderRequest, session: SessionDep, _: StaffUser
):
    await get_or_404(session, Lesson, lesson_id, "Урок не найден")
    questions = await load_lesson_questions(session, lesson_id)
    ordered = apply_order(questions, payload.ids)
    await session.commit()
    return ordered
