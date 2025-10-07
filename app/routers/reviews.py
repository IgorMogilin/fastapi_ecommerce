from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_buyer
from app.db_depends import get_async_db
from app.models.products import Product
from app.models.reviews import Review
from app.models.users import User as UserModel
from app.schemas import ReviewCreate, ReviewResponse

router = APIRouter(
    tags=['reviews'],
)


@router.get(
    '/reviews/',
    response_model=List[ReviewResponse],
)
async def get_all_active_reviews(
    db: AsyncSession = Depends(get_async_db)
) -> List[ReviewResponse]:
    """Получает список всех активных отзывов."""
    result = await db.scalars(
        select(Review)
        .where(Review.is_active)
    )
    return result.all()


@router.get(
    '/products/{product_id}/reviews/',
    response_model=List[ReviewResponse],
)
async def get_reviews_for_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> List[ReviewResponse]:
    """Получает список всех отзывов на данный товар."""
    request_product = await db.scalars(
        select(Product)
        .where(Product.id == product_id)
        .where(Product.is_active)
    )
    if not request_product.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Товар не найден'
        )
    result = await db.scalars(
        select(Review)
        .where(Review.product_id == product_id)
        .where(Review.is_active)
    )
    return result.all()


@router.post(
    '/reviews/',
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    review: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_buyer)
) -> ReviewResponse:
    """Создает новый отзыв на товар."""
    prepare_product = await db.scalar(
        select(Product)
        .where(Product.id == review.product_id)
        .where(Product.is_active)
    )
    if not prepare_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Продукт не найден'
        )
    product_reviews = await db.scalars(
        select(Review.grade)
        .where(Review.product_id == prepare_product.id)
        .where(Review.is_active)
    )
    result_reviews = product_reviews.all()
    sum_raiting = (
        sum(result_reviews) + review.grade
        ) / (len(result_reviews) + 1)
    await db.execute(
        update(Product)
        .where(Product.id == review.product_id)
        .values(rating=sum_raiting)
    )
    new_review = Review(
        **review.model_dump(),
        user_id=current_user.id,
    )
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review


@router.delete(
    '/reviews/{review_id}'
)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_admin),
) -> dict:
    """Удаляет отзыв на товар по ID."""
    request_review = await db.scalar(
        select(Review)
        .where(Review.id == review_id)
        .where(Review.is_active)
    )
    if not request_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Отзыв не найден или не активен'
        )
    product_reviews = await db.scalars(
        select(Review.grade)
        .where(Review.product_id == request_review.product_id)
        .where(Review.is_active)
        .where(Review.id != request_review.id)
    )
    result_reviews = product_reviews.all()
    if not result_reviews:
        sum_raiting = 0.00
    else:
        sum_raiting = sum(result_reviews) / len(result_reviews)
    await db.execute(
        update(Product)
        .where(Product.id == request_review.product_id)
        .values(rating=sum_raiting)
    )
    if current_user:
        await db.execute(
            update(Review)
            .where(Review.id == review_id)
            .values(is_active=False)
        )
    await db.commit()
    return {"message": "Review deleted"}
