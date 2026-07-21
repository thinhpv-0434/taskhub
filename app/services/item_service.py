from typing import Dict, Optional
from uuid import uuid4

from ..schemas.item import ItemCreate, ItemRead


class ItemService:
    def __init__(self, db: Dict):
        self.db = db

    def create(self, payload: ItemCreate) -> ItemRead:
        item_id = str(uuid4())
        item = {"id": item_id, "name": payload.name, "description": payload.description}
        if "items" not in self.db:
            self.db["items"] = {}
        self.db["items"][item_id] = item
        return ItemRead(**item)

    def get(self, item_id: str) -> Optional[ItemRead]:
        item = self.db.get("items", {}).get(item_id)
        if not item:
            return None
        return ItemRead(**item)
