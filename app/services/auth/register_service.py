from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.dto.user import UserRegisterDTO
from app.core.exceptions import DatabaseIntegrityError
from app.core.security import hash_password
from app.models.user import User


async def register_service(register_data: UserRegisterDTO, db: AsyncSession) -> User:
    hashed_password = await hash_password(register_data.password1.get_secret_value())
    try:
        new_user = User(id=uuid4(), email=register_data.email, password=hashed_password)
    
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return new_user
    except IntegrityError as e:
        await db.rollback()
        raise DatabaseIntegrityError(f'User already exists: {e}')
