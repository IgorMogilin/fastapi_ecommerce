from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_depends import get_async_db
from app.models import Category as CategoryModel
from app.models import Product as ProductModel
from app.schemas import Product as ProductSchema
from app.schemas import ProductCreate

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get(
        "/",
        response_model=list[ProductSchema],
        status_code=status.HTTP_200_OK
    )
async def get_all_products(
    db: AsyncSession = Depends(get_async_db)
) -> list[ProductSchema]:
    """Возвращает список всех товаров."""
    result = await db.scalars(
        select(ProductModel).where(ProductModel.is_active)
    )
    return result.all() or []


@router.post(
        "/",
        response_model=ProductCreate,
        status_code=status.HTTP_201_CREATED
        )
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db)
) -> ProductCreate:
    """Создаёт новый товар."""
    smt = select(CategoryModel).where(
            CategoryModel.id == product.category_id,
            CategoryModel.is_active
        )
    pre_category_result = await db.scalars(smt)
    category_result = pre_category_result.first()
    if not category_result:
        raise HTTPException(
            status_code=400,
            detail="Category not found"
        )
    db_product = ProductModel(**product.model_dump(), is_active=True)
    db.add(db_product)
    await db.commit()
    return db_product


@router.get(
        "/category/{category_id}",
        response_model=list[ProductSchema],
        status_code=status.HTTP_200_OK
    )
async def get_products_by_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> list[ProductSchema]:
    """Возвращает список товаров в указанной категории по её ID."""
    smt = select(CategoryModel).where(CategoryModel.id == category_id)
    pre_request_category = await db.scalars(smt)
    request_category = pre_request_category.first()
    if not request_category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    result = await db.scalars(select(ProductModel).where(
        ProductModel.category_id == category_id,
        ProductModel.is_active
    ))
    return result.all() or []


@router.get(
        "/{product_id}",
        response_model=ProductSchema,
        status_code=status.HTTP_200_OK
    )
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> ProductSchema:
    """Возвращает детальную информацию о товаре по его ID."""
    smt = select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active
    )
    pre_request_product = await db.scalars(smt)
    request_product = pre_request_product.first()
    if not request_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    request_category = request_product.category_id
    smt2 = select(CategoryModel).where(
        CategoryModel.id == request_category,
        CategoryModel.is_active
    )
    pre_result = await db.scalars(smt2)
    result = pre_result.first()
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Category not found"
        )
    return request_product


@router.put(
        "/{product_id}",
        response_model=ProductCreate,
        status_code=status.HTTP_200_OK
    )
async def update_product(
    product_id: int,
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db)
) -> ProductCreate:
    """Обновляет товар по его ID."""
    stmt = select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active
    )
    pre_request_product = await db.scalars(stmt)
    request_product = pre_request_product.first()
    if not request_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    request_category = request_product.category_id
    smt2 = select(CategoryModel).where(
        CategoryModel.id == request_category,
        CategoryModel.is_active
    )
    pre_result = await db.scalars(smt2)
    result = pre_result.first()
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Category not found"
        )
    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product.model_dump())
    )
    await db.commit()
    return request_product


@router.delete(
        "/{product_id}",
        status_code=status.HTTP_200_OK
    )
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """Удаляет товар по его ID."""
    stmt = select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active
    )
    pre_request_product = await db.scalars(stmt)
    request_product = pre_request_product.first()
    if not request_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    request_category = request_product.category_id
    smt2 = select(CategoryModel).where(
        CategoryModel.id == request_category,
        CategoryModel.is_active
    )
    pre_result = await db.scalars(smt2)
    result = pre_result.first()
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Category not found"
        )
    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(is_active=False)
    )
    await db.commit()
    return {"status": "success", "message": "Product marked as inactive"}
