from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import connect_to_mongo, close_mongo_connection, db
from backend.app.middleware.logging_middleware import AuditLoggingMiddleware
from backend.app.routers import auth, users, knowledge, documents, chat, analytics, settings as user_settings, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    from backend.app.services.intent_service import load_dynamic_entities
    await load_dynamic_entities()
    yield
    await close_mongo_connection()

from fastapi import Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="INGRES Virtual Assistant API",
    description="AI-Driven ChatBOT for INGRES (Integrated Groundwater Information Retrieval System)",
    version="2.0.0",
    lifespan=lifespan
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Internal Server Error: {str(exc)}", "data": None}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL] if settings.FRONTEND_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditLoggingMiddleware)

# Include All Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(knowledge.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(user_settings.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Welcome to INGRES Virtual Assistant API v2.0",
        "data": {
            "version": "2.0.0",
            "status": "online"
        }
    }

@app.get("/api/v1/health")
async def health_check():
    db_connected = False
    collections = []
    if db.db is not None:
        try:
            collections = await db.db.list_collection_names()
            db_connected = True
        except Exception:
            db_connected = False

    return {
        "success": True,
        "message": "INGRES Service Operational",
        "data": {
            "status": "healthy" if db_connected else "degraded",
            "database_connected": db_connected,
            "database_name": settings.DATABASE_NAME,
            "active_collections": collections,
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "firebase_configured": bool(settings.FIREBASE_PROJECT_ID)
        }
    }
