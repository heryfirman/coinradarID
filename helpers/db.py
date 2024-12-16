from pymongo import MongoClient
import os

MONGODB_URI = os.environ["MONGODB_URI"]
DB_NAME = os.environ["DB_NAME"]
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]