import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

def get_db():
    client = MongoClient(MONGO_URI)
    return client["ezlife"]
