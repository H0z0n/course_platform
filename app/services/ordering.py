from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.models import Lesson, Module, QuizQuestion


async def next_position(
    session: AsyncSession, column: InstrumentedAttribute[int], *where: ColumnElement[bool]
) -> int:
    current_max = await session.scalar(select(func.max(column)).where(*where))
    return (current_max or 0) + 1


def apply_order[T: (Module, Lesson, QuizQuestion)](items: Sequence[T], ids: list[int]) -> list[T]:
    items_by_id = {item.id: item for item in items}
    if len(ids) != len(items_by_id) or set(ids) != set(items_by_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "ids должен содержать каждый элемент ровно один раз",
        )
    for position, item_id in enumerate(ids, start=1):
        items_by_id[item_id].position = position
    return [items_by_id[item_id] for item_id in ids]
