from fastapi import FastAPI, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from services.schema_discovery import SchemaDiscovery
from services.simple_document_processor import SimpleDocumentProcessor as DocumentProcessor
from services.query_engine import QueryEngine
from services.cache import CacheService
from api.routes import query, ingestion
from core.config import settings

# Global state management
_document_processor = None
_query_engine = None
_db_schema = None
_db_connection_string = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global _document_processor
    _document_processor = DocumentProcessor()
    print("Application started - Document processor initialized")
    yield
    print("Application shutdown")

app = FastAPI(
    title='NLP Query Engine',
    description='Natural Language Query Engine for Employee Data with Hybrid Search',
    version='1.0.0',
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add debug middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    path = request.url.path
    method = request.method
    print(f"\n=== Request ===")
    print(f"Method: {method}")
    print(f"Path: {path}")
    print(f"Headers: {dict(request.headers)}")
    
    if method == "POST":
        body = await request.body()
        if body:
            try:
                print(f"Request body: {body.decode()}")
            except:
                print("Could not decode request body")
    
    response = await call_next(request)
    print(f"\n=== Response ===")
    print(f"Status: {response.status_code}")
    return response

# API router configuration
api_router = APIRouter(prefix="/api")

# Add sub-routers
api_router.include_router(ingestion.router, tags=["ingestion"])
api_router.include_router(query.router, tags=["query"])

# Include the main API router
app.include_router(api_router)

# Log available routes
print("\n=== Available Routes ===")
for route in app.routes:
    if hasattr(route, "methods") and route.path != "/openapi.json":
        print(f"{route.methods} {route.path}")

# Global state management functions
def get_document_processor() -> DocumentProcessor:
    return _document_processor

def get_query_engine() -> QueryEngine:
    global _query_engine, _db_schema, _db_connection_string
    if not _query_engine and _db_schema and _db_connection_string:
        _query_engine = QueryEngine(
            db_schema=_db_schema,
            document_processor=_document_processor,
            db_connection_string=_db_connection_string
        )
    return _query_engine

def set_database_connection(connection_string: str, schema: dict):
    global _db_schema, _db_connection_string, _query_engine
    _db_schema = schema
    _db_connection_string = connection_string
    _query_engine = None  # Reset query engine to force recreation

def add_documents(documents: dict):
    """Add documents to the document processor"""
    # This would be handled by the document processor's internal state
    pass

def get_document_store() -> dict:
    """Get document store from processor"""
    return {}  # This would return the actual document store

def remove_document(filename: str) -> bool:
    """Remove document from store"""
    return True  # This would actually remove the document

@app.get("/")
def root():
    return {
        "message": "NLP Query Engine API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database_connected": _db_schema is not None,
        "documents_loaded": _document_processor.get_document_count() if _document_processor else 0
    }
