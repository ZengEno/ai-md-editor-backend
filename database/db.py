import os
from motor import motor_asyncio


client = motor_asyncio.AsyncIOMotorClient(os.getenv('mongodb_connection_string'))
db = client.AI_Article_Editor_DB


# run the following code to initiate the database
# user_profiles.create_index("uid", unique=True)
# user_profiles.create_index("phone_number", unique=True)