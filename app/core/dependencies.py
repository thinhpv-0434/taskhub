from fastapi import Depends, Request

from ..services.item_service import ItemService


def get_db(request: Request):
    return request.app.state.db


def get_item_service(db=Depends(get_db)) -> ItemService:
    return ItemService(db)
