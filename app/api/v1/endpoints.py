from fastapi import APIRouter, Depends, HTTPException, status

from ...core.dependencies import get_item_service
from ...schemas.item import ItemCreate, ItemRead
from ...services.item_service import ItemService


router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, service: ItemService = Depends(get_item_service)) -> ItemRead:
    return service.create(payload)
@router.get("/items/{item_id}", response_model=ItemRead)
def get_item(item_id: str, service: ItemService = Depends(get_item_service)) -> ItemRead:
    item = service.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
