from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import session

from app.db_depends import get_db
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
    db: session = Depends(get_db)
) -> list[ProductSchema]:
    """Возвращает список всех товаров."""
    result = db.scalars(
        select(ProductModel).where(ProductModel.is_active)
    ).all()
    return result or []


@router.post(
        "/",
        response_model=ProductCreate,
        status_code=status.HTTP_201_CREATED
        )
async def create_product(
    product: ProductCreate,
    db: session = Depends(get_db)
) -> ProductCreate:
    """Создаёт новый товар."""
    smt = select(CategoryModel).where(
            CategoryModel.id == product.category_id,
            CategoryModel.is_active
        )
    category_result = db.scalars(smt).first()
    if not category_result:
        raise HTTPException(
            status_code=400,
            detail="Category not found"
        )
    db_product = ProductModel(**product.model_dump(), is_active=True)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get(
        "/category/{category_id}",
        response_model=list[ProductSchema],
        status_code=status.HTTP_200_OK
    )
async def get_products_by_category(
    category_id: int,
    db: session = Depends(get_db)
) -> list[ProductSchema]:
    """Возвращает список товаров в указанной категории по её ID."""
    smt = select(CategoryModel).where(CategoryModel.id == category_id)
    request_category = db.scalars(smt).first()
    if not request_category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    result = db.scalars(select(ProductModel).where(
        ProductModel.category_id == category_id,
        ProductModel.is_active
    )).all()
    return result or []


@router.get(
        "/{product_id}",
        response_model=ProductSchema,
        status_code=status.HTTP_200_OK
    )
async def get_product(
    product_id: int,
    db: session = Depends(get_db)
) -> ProductSchema:
    """Возвращает детальную информацию о товаре по его ID."""
    smt = select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active
    )
    request_product = db.scalars(smt).first()
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
    result = db.scalars(smt2).first()
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
    db: session = Depends(get_db)
) -> ProductCreate:
    """Обновляет товар по его ID."""
    stmt = select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active
    )
    request_product = db.scalars(stmt).first()
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
    result = db.scalars(smt2).first()
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Category not found"
        )
    db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product.model_dump())
    )
    db.commit()
    db.refresh(request_product)
    return request_product


@router.delete(
        "/{product_id}",
        status_code=status.HTTP_200_OK
    )
async def delete_product(
    product_id: int,
    db: session = Depends(get_db)
) -> dict:
    """Удаляет товар по его ID."""
    stmt = select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active
    )
    request_product = db.scalars(stmt).first()
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
    result = db.scalars(smt2).first()
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Category not found"
        )
    db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(is_active=False)
    )
    db.commit()
    return {"status": "success", "message": "Product marked as inactive"}
