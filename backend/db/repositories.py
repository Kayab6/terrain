from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from bson import ObjectId
from pymongo import ReturnDocument


def _public_id(value):
    return str(value)


def _utc_now():
    return datetime.now(timezone.utc)


class MemoryRepository:
    def __init__(self):
        self._items = {}
        self._lock = RLock()

    def create(self, payload):
        item = deepcopy(payload)
        item["id"] = item.get("id") or uuid4().hex
        item["createdAt"] = _utc_now().isoformat()
        item["updatedAt"] = item["createdAt"]
        with self._lock:
            self._items[item["id"]] = item
        return deepcopy(item)

    def list(self):
        with self._lock:
            return [deepcopy(item) for item in reversed(list(self._items.values()))]

    def get(self, item_id):
        with self._lock:
            item = self._items.get(str(item_id))
        return deepcopy(item) if item is not None else None

    def update(self, item_id, payload):
        with self._lock:
            if item_id not in self._items:
                return None
            item = deepcopy(payload)
            item["id"] = item_id
            item["createdAt"] = self._items[item_id].get("createdAt")
            item["updatedAt"] = _utc_now().isoformat()
            self._items[item_id] = item
            return deepcopy(item)

    def delete(self, item_id):
        with self._lock:
            return self._items.pop(str(item_id), None) is not None


class MongoRepository:
    def __init__(self, database, collection_name):
        self._collection = database[collection_name]

    def create(self, payload):
        document = deepcopy(payload)
        document["_id"] = ObjectId()
        document["createdAt"] = _utc_now()
        document["updatedAt"] = document["createdAt"]
        self._collection.insert_one(document)
        return self._format(document)

    def list(self):
        return [
            self._format(document)
            for document in self._collection.find().sort("createdAt", -1)
        ]

    def get(self, item_id):
        try:
            query = {"_id": ObjectId(item_id)}
        except (TypeError, ValueError):
            return None
        document = self._collection.find_one(query)
        return self._format(document) if document else None

    def update(self, item_id, payload):
        try:
            query = {"_id": ObjectId(item_id)}
        except (TypeError, ValueError):
            return None
        document = deepcopy(payload)
        document["updatedAt"] = _utc_now()
        document.pop("_id", None)
        updated = self._collection.find_one_and_update(
            query, {"$set": document}, return_document=ReturnDocument.AFTER
        )
        return self._format(updated) if updated else None

    def delete(self, item_id):
        try:
            query = {"_id": ObjectId(item_id)}
        except (TypeError, ValueError):
            return False
        return self._collection.delete_one(query).deleted_count > 0

    def _format(self, document):
        formatted = deepcopy(document)
        formatted["id"] = _public_id(formatted.pop("_id"))
        formatted["createdAt"] = (
            formatted["createdAt"].isoformat()
            if isinstance(formatted.get("createdAt"), datetime)
            else formatted.get("createdAt")
        )
        formatted["updatedAt"] = (
            formatted["updatedAt"].isoformat()
            if isinstance(formatted.get("updatedAt"), datetime)
            else formatted.get("updatedAt")
        )
        return formatted
