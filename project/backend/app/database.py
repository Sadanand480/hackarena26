import os
from pymongo import MongoClient


class MongoRepo:
    def __init__(self) -> None:
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        mongo_db = os.getenv("MONGO_DB", "cctv_threat_detection")
        self.client = MongoClient(mongo_url)
        self.db = self.client[mongo_db]
        self.events = self.db["events"]

    def insert_event(self, payload: dict) -> str:
        result = self.events.insert_one(payload)
        return str(result.inserted_id)

    def list_events(self, limit: int = 50) -> list[dict]:
        return list(self.events.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))

    def clear_events(self) -> None:
        self.events.delete_many({})
