import uvicorn
import os
import dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from routers.auth import auth_router
from routers.agent import agent_router
from routers.chat import chat_router

# this is used to set up the environment variables
dotenv.load_dotenv()

app = FastAPI()
app.include_router(auth_router)
app.include_router(agent_router, prefix='/agent')
app.include_router(chat_router, prefix='/chat')

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://192.168.71.113:8081",
    "https://127.0.0.1:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# redirect the root to the docs
@app.get("/", include_in_schema=False)
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=8080, reload=True)

