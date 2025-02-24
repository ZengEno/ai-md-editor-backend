import uvicorn
import os
import dotenv

# this is used to set up the environment variables
dotenv.load_dotenv(encoding='utf-8', override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from routers.auth import auth_router
from routers.agent import agent_router
from routers.chat import chat_router
from database.db import client, db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # this will be run when start the app
    try:
        # check if the mongodb is connected
        await client.admin.command('ping')
        print('    MongoDB connected successfully!')

        # Ensure the database exists
        db_list = await client.list_database_names()
        if "ai_md_editor_db" not in db_list:
            print("    Database ai_md_editor_db does not exist. It will be created upon first write.")

        # Check and initialize collections if they do not exist
        collections = await db.list_collection_names()
        required_collections = ["app_statistics", "assistant_data", "user_profiles"]

        for collection in required_collections:
            if collection not in collections:
                await db.create_collection(collection)
                print(f"    Created collection: {collection}")

        # Check and insert initial document in app_statistics if it doesn't exist
        app_stats_collection = db.app_statistics
        existing_doc = await app_stats_collection.find_one({"name": "registration_count"})

        if existing_doc is None:
            initial_doc = {"name": "registration_count", "value": 0}
            await app_stats_collection.insert_one(initial_doc)
            print("    Inserted initial document in app_statistics: ", initial_doc)
    except Exception as e:
        print(f"    Failed to connect to MongoDB: {e}")

    # yield the app (run the app)
    yield

    # this will be run when shutdown the app
    print("    Shutting down MongoDB connection...")


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix='/api')
app.include_router(agent_router, prefix='/api/agent')
app.include_router(chat_router, prefix='/api/chat')

origins = [
    "http://localhost",
    "http://localhost:5173", # the frontend local development port
    "http://frontend:80", # the nginx port when running in docker
    "https://frontend:80",
    "https://enolearnai.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # redirect the root to the docs
# @app.get("/", include_in_schema=False)
# async def redirect_root_to_docs():
#     return RedirectResponse("/docs")


if __name__ == "__main__":
    should_reload = os.getenv("ENV") != "production"  # reload only when the environment is not production
    uvicorn.run("main:app", host='0.0.0.0', port=8080, reload=should_reload)  # Set reload based on environment

