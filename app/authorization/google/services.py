from sqlalchemy import select

from app.database.models import UserBase, Role


def get_user_by_email(session_db, email: str) -> UserBase | None:
    result = session_db.execute(select(UserBase).filter_by(email=email))
    return result.scalar_one_or_none()


def create_user(session_db, email: str, username: str) -> UserBase:
    new_user = UserBase(
        username=username, email=email, is_active=True, role=Role.USER
    )

    session_db.add(new_user)
    session_db.commit()
    session_db.refresh(new_user)

    return new_user
