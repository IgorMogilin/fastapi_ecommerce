from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db
from app.models.reviews import Review
from app.models.products import Product
from app.schemas import ReviewCreate, ReviewResponse
from typing import List


router = APIRouter(
    tags=['reviews'],
)


@router.get(
    '/reviews/',
    response_model=List[ReviewResponse],
)
async def get_all_active_reviews(
    db: AsyncSession = Depends(get_async_db)
):
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
):
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
):
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
    sum_raiting = (sum(result_reviews) + review.grade) / (len(result_reviews) + 1)
    await db.execute(
        update(Product)
        .where(Product.id == review.product_id)
        .values(rating=sum_raiting)
    )
    new_review = Review(**review.model_dump())
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review


@router.delete(
    '/reviews/{review_id}'
)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_all_active_reviews)
) -> dict:
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
