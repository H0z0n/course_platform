from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


async def get_or_404[T](session: AsyncSession, model: type[T], object_id: int, detail: str) -> T:
    obj = await session.get(model, object_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
    return obj
