from pymongo.mongo_client import MongoClient


DB_NAME = "aichords"


uri = "mongodb://aichords:12345@mongo:27017/aichords"


mongodb_client = MongoClient(uri)
database = mongodb_client[DB_NAME]


__all__ = ["database"]
