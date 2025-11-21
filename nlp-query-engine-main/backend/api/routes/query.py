from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
from services.query_engine import QueryEngine
from services.cache import CacheService
from core.config import settings

router = APIRouter()

print("Initializing query router")

class QueryRequest(BaseModel):
    query: str
    queryType: str  # 'sql' or 'document'
    use_cache: bool = True

class QueryResponse(BaseModel):
    query_type: str
    results: Union[List[dict], Dict[str, Any]]
    execution_time: float
    cached: bool = False
    error: Optional[str] = None

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    cache_service: CacheService = Depends()
):
    """
    Process natural language queries against both database and documents
    """
    import time
    start_time = time.time()
    
    try:
        # Add some default preprocessing for document queries
        query = request.query.lower()
        if any(keyword in query for keyword in ["document", "resume", "text", "content"]):
            request.query = f"find document containing {request.query}"
        
        # Check cache first if enabled
        if request.use_cache:
            cached_result = await cache_service.get_query_result(request.query)
            if cached_result:
                return QueryResponse(
                    query_type=cached_result["query_type"],
                    results=cached_result["results"],
                    execution_time=time.time() - start_time,
                    cached=True
                )
        
        # Get query engine instance (this would be injected via dependency)
        # For now, we'll create it here - in production, use dependency injection
        from main import get_query_engine
        engine = get_query_engine()
        
        if not engine:
            raise HTTPException(
                status_code=400, 
                detail="Database not connected. Please connect to a database first."
            )
        
        # Process the query based on type
        if request.queryType == 'sql':
            result = {
                "query_type": "sql",
                "results": engine.generate_and_execute_sql(request.query),
                "execution_time": time.time() - start_time
            }
        else:  # document query
            result = {
                "query_type": "document",
                "results": engine.search_documents(request.query),
                "execution_time": time.time() - start_time
            }
        
        # Cache the result if enabled
        if request.use_cache and not result.get("error"):
            await cache_service.set_query_result(request.query, result)
        
        execution_time = time.time() - start_time
        
        return QueryResponse(
            query_type=result.get("query_type", "unknown"),
            results=result.get("results", []),
            execution_time=execution_time,
            cached=False,
            error=result.get("error")
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        return QueryResponse(
            query_type="error",
            results=[],
            execution_time=execution_time,
            error=str(e)
        )

@router.get("/query/history")
async def get_query_history(
    limit: int = 50,
    cache_service: CacheService = Depends()
):
    """
    Get query history from cache
    """
    try:
        history = await cache_service.get_query_history(limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/query/cache")
async def clear_cache(cache_service: CacheService = Depends()):
    """
    Clear query cache
    """
    try:
        await cache_service.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))