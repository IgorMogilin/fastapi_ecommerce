from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_depends import get_async_db
from app.models.categories import Category as CategoryModel
from app.schemas import Category as CategorySchema, CategoryCreate


router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/", response_model=list[CategorySchema])
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных категорий.
    """
    stmt = select(CategoryModel).where(CategoryModel.is_active)
    categories = await db.scalars(stmt)
    return categories.all()


@router.post(
        "/",
        response_model=CategorySchema,
        status_code=status.HTTP_201_CREATED
    )
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_async_db)
) -> CategorySchema:
    """Создаёт новую категорию."""
    if category.parent_id is not None:
        stmt = select(CategoryModel).where(
            CategoryModel.id == category.parent_id,
            CategoryModel.is_active
        )
        parent = await db.scalars(stmt)
        parent_i = parent.first()
        if parent_i is None:
            raise HTTPException(
                status_code=400,
                detail="Parent category not found"
            )
    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    return db_category


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    db: AsyncSession = Depends(get_async_db)
) -> CategorySchema:
    """Обновляет категорию по её ID."""
    stmt = select(CategoryModel).where(CategoryModel.id == category_id,
                                       CategoryModel.is_active)
    db_category = await db.scalars(stmt)
    db_category_i = db_category.first()
    if db_category_i is None:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.parent_id is not None:
        parent_stmt = select(CategoryModel).where(
            CategoryModel.id == category.parent_id,
            CategoryModel.is_active
        )
        parent = await db.scalars(parent_stmt)
        parent_i = parent.first()
        if parent_i is None:
            raise HTTPException(
                status_code=400,
                detail="Parent category not found"
            )
    await db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**category.model_dump())
    )
    await db.commit()
    return db_category_i


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """Логически удаляет категорию по её ID, устанавливая is_active=False."""
    stmt = select(CategoryModel).where(
        CategoryModel.id == category_id,
        CategoryModel.is_active
    )
    category = await db.scalars(stmt)
    category_i = category.first()
    if category_i is None:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.execute(update(CategoryModel).where(
        CategoryModel.id == category_id).values(is_active=False)
    )
    await db.commit()
    return {"status": "success", "message": "Category marked as inactive"}
