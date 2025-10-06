from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id'),
        nullable=False
    )
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    comment_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint('grade >= 1 AND grade <= 5', name='check_grade_range'),
    )
