import json
import time
from typing import Dict, List, Optional, Any
from core.config import settings
import hashlib

class CacheService:
    def __init__(self):
        self.cache = {}
        self.query_history = []
        self.ttl = settings.CACHE_TTL
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate a cache key for the query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    async def get_query_result(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached query result if it exists and is not expired"""
        cache_key = self._generate_cache_key(query)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            
            # Check if cache is still valid
            if time.time() - cached_data['timestamp'] < self.ttl:
                print(f"Cache hit for query: {query[:50]}...")
                return cached_data['result']
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
                print(f"Cache expired for query: {query[:50]}...")
        
        return None
    
    async def set_query_result(self, query: str, result: Dict[str, Any]) -> None:
        """Cache query result"""
        cache_key = self._generate_cache_key(query)
        
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time(),
            'query': query
        }
        
        # Add to query history
        self.query_history.append({
            'query': query,
            'timestamp': time.time(),
            'query_type': result.get('query_type', 'unknown'),
            'result_count': len(result.get('results', []))
        })
        
        # Keep only last 100 queries in history
        if len(self.query_history) > 100:
            self.query_history = self.query_history[-100:]
        
        print(f"Cached result for query: {query[:50]}...")
    
    async def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get query history"""
        return self.query_history[-limit:]
    
    async def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
        self.query_history.clear()
        print("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'history_size': len(self.query_history),
            'ttl': self.ttl
        }