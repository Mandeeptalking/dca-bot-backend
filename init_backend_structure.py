import os

BASE_DIR = "."

structure = {
    "": ["main.py", ".env", "requirements.txt", "README.md"],
    "app": ["__init__.py", "supabase_client.py"],
    "app/routers": ["bots.py"],
    "app/models": ["bot.py"],
    "app/services": ["bot_service.py"],
    "app/utils": ["logger.py"],
}

base_content = {
    "main.py": '''from fastapi import FastAPI
from app.routers import bots

app = FastAPI()

app.include_router(bots.router, prefix="/bots", tags=["Bots"])

@app.get("/")
def read_root():
    return {"message": "DCA Bot Backend running"}
''',
    "app/supabase_client.py": '''from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
''',
    "requirements.txt": '''fastapi
uvicorn
supabase
python-dotenv
requests
''',
    "app/routers/bots.py": '''from fastapi import APIRouter
from app.services import bot_service

router = APIRouter()

@router.get("/")
def get_bots():
    return bot_service.get_all_bots()
''',
    "app/services/bot_service.py": '''from app.supabase_client import supabase

def get_all_bots():
    response = supabase.table("bots").select("*").limit(10).execute()
    return response.data
''',
    "app/models/bot.py": '''from pydantic import BaseModel
from typing import Optional

class Bot(BaseModel):
    id: Optional[str]
    name: str
    type: str
    exchange: str
    trading_pair: str
''',
    "app/utils/logger.py": '''import logging

logger = logging.getLogger("bot_backend")
logging.basicConfig(level=logging.INFO)
''',
    "README.md": "# DCA Bot Backend\n\nFastAPI backend for managing DCA trading bots with Supabase.",
    ".env": "SUPABASE_URL=\nSUPABASE_SERVICE_ROLE_KEY=",
}

# Create folders and files
for folder, files in structure.items():
    folder_path = os.path.join(BASE_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    for file in files:
        full_path = os.path.join(folder_path, file)
        with open(full_path, "w") as f:
            content = base_content.get(os.path.join(folder, file), "")
            f.write(content)

print(f"✅ Project structure created under ./{BASE_DIR}")
