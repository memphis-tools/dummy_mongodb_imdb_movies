"""The Mongodb engine"""

import os
import urllib.parse
from pymongo import MongoClient, ASCENDING

# MongoDB connection settings
mongo_user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
mongo_server = os.getenv("MONGO_SERVER")
mongo_port = int(os.getenv("MONGO_PORT"))
mongo_db = os.getenv("MONGO_DB")
mongo_test_db = os.getenv("MONGO_TEST_DB")

# URL encode username and password
encoded_user = urllib.parse.quote_plus(mongo_user)
encoded_password = urllib.parse.quote_plus(mongo_password)

# Ensure that required environment variables are set
if not (mongo_user and mongo_password and mongo_server and mongo_db):
    raise RuntimeError("MongoDB environment variables not properly set.")

# MongoDB client setup
client = MongoClient(
    f"mongodb://{encoded_user}:{encoded_password}@{mongo_server}:{mongo_port}/",
    uuidRepresentation="standard",
)
db = client[mongo_db]
test_db = client[mongo_test_db]

for old_db in [mongo_db, mongo_test_db]:
    if old_db in client.list_database_names():
        client.drop_database(old_db)

collection = db["movies"]
collection.create_index([("title", ASCENDING)], unique=True)

test_collection = test_db["movies"]
test_collection.create_index([("title", ASCENDING)], unique=True)
