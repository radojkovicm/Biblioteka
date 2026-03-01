import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

# Load env
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

from app.database import init_db, get_db
from app.utils.scheduler import start_scheduler, stop_scheduler
from app.utils.auth import decode_token
from app.models.staff import Staff
from app.models.user_permission import UserPermission
from app.routes import auth, books, members, loans, reservations, reports, settings, import_export

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("biblioteka")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Starting scheduler...")
    start_scheduler()
    yield
    logger.info("Stopping scheduler...")
    stop_scheduler()


app = FastAPI(
    title="Biblioteka — Sistem upravljanja",
    version="1.0.0",
    lifespan=lifespan,
)

# Static files and templates
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# API Routes
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(members.router)
app.include_router(loans.router)
app.include_router(reservations.router)
app.include_router(reports.router)
app.include_router(settings.router)
app.include_router(import_export.router)


def _page_user(request: Request, db: Session):
    """Resolve logged-in Staff from the access_token cookie. Returns None if missing/invalid."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        return db.query(Staff).filter(Staff.id == user_id, Staff.is_active == True).first()
    except Exception:
        return None


# HTML Pages
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/knjige", response_class=HTMLResponse)
async def books_page(request: Request):
    return templates.TemplateResponse("books.html", {"request": request})


@app.get("/clanovi", response_class=HTMLResponse)
async def members_page(request: Request):
    return templates.TemplateResponse("members.html", {"request": request})


@app.get("/rezervacije", response_class=HTMLResponse)
async def reservations_page(request: Request):
    return templates.TemplateResponse("reservations.html", {"request": request})


@app.get("/izvestaji", response_class=HTMLResponse)
async def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


@app.get("/podesavanja", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    user = _page_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    if not user.is_admin:
        perms = {
            p.module: p
            for p in db.query(UserPermission).filter(UserPermission.user_id == user.id).all()
        }
        has_settings = bool(perms.get("settings") and perms["settings"].can_read)
        has_books_write = bool(perms.get("books") and perms["books"].can_write)
        if not has_settings and not has_books_write:
            return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("settings.html", {"request": request})
