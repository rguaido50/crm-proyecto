from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from crm.contacts.router import router as contacts_api_router
from crm.contacts.views import router as contacts_views_router

BASE_DIR = Path(__file__).parent

app = FastAPI(title="itela CRM")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(contacts_api_router)
app.include_router(contacts_views_router)
