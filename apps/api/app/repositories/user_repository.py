from app.repositories.base import BaseRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserBase

class UserRepository(BaseRepository[User, UserCreate, UserBase]):
    pass

user_repo = UserRepository(User)
