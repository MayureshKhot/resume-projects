import os
import time
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text, pool
from sqlalchemy.pool import QueuePool
import openai
from core.config import settings

class QueryEngine:
    def __init__(self, db_schema: Dict, document_processor, db_connection_string: str):
        self.db_schema = db_schema
        self.document_processor = document_processor
        self.db_connection_string = db_connection_string
        
        # database connection with connection pooling
        self.engine = create_engine(
            db_connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Initialize Groq client
        self.client = openai.OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        print("Query Engine Initialized with Groq and connection pooling.")
        
    def classify_query(self, query: str) -> str:
        """Classify query type with improved logic"""
        print(f"Classifying query: '{query}'")
        
        sql_keywords = [
            "employee", "salary", "department", "hired", "average", "count", "sum", "max", "min",
            "table", "database", "query", "select", "from", "where", "group by", "order by",
            "join", "inner", "left", "right", "union", "distinct", "having"
        ]
        
        doc_keywords = [
            "skill", "resume", "experience", "review", "performance", "document", "file",
            "text", "content", "search", "find", "look for", "contains", "mentions"
        ]
        
        hybrid_keywords = [
            "both", "combine", "together", "all", "everything", "complete", "full"
        ]
        
        query_lower = query.lower()
        
        # Check for hybrid queries
        if any(keyword in query_lower for keyword in hybrid_keywords):
            print("-> Classified as HYBRID query")
            return "HYBRID"
        
        # Count keyword matches
        sql_matches = sum(1 for keyword in sql_keywords if keyword in query_lower)
        doc_matches = sum(1 for keyword in doc_keywords if keyword in query_lower)
        
        if sql_matches > doc_matches:
            print("-> Classified as SQL query")
            return "SQL"
        elif doc_matches > sql_matches:
            print("-> Classified as DOCUMENT query")
            return "DOCUMENT"
        else:
            # Default to hybrid for ambiguous queries
            print("-> Defaulting to HYBRID query")
            return "HYBRID"
        
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search documents using semantic similarity"""
        print(f"Searching documents for: '{query}'")
        
        if not self.document_processor:
            print("-> No document processor available")
            return []
        
        print(f"-> Document processor has {self.document_processor.get_document_count()} documents")
        
        # Clean up query for document search
        cleaned_query = query.lower().strip()
        if not any(term in cleaned_query for term in ["find", "search", "show", "get"]):
            cleaned_query = f"find {cleaned_query}"
        
        # Use semantic search
        results = self.document_processor.search_similar_documents(cleaned_query, top_k)
        
        print(f"-> Found {len(results)} matching documents.")
        return results  # Return the original results without reformatting
    
    def generate_and_execute_sql(self, query: str) -> List[Dict[str, Any]]:
        print("Generating SQL query with LLM...")
        
        # Create detailed schema description
        schema_description = self._format_schema_for_llm()
        
        prompt = f"""
        You are an expert database engineer. Given the following database schema:
        {schema_description}
        
        User question: {query}
        
        Write a single, valid SQL query to answer the question. Use the exact table and column names from the schema.
        - For SELECT queries: Return the requested data
        - For INSERT queries: Add the record with the specified values
        - For UPDATE queries: Modify the specified records
        - For DELETE queries: Remove the specified records
        
        DO NOT add any explanation, commentary, or markdown formatting.
        Only return the raw SQL query.
        Your output must contain only one valid SQL statement. Do not include semicolons unless they are strictly part of the SQL dialect, and never include more than one full statement.
        """
        
        try:
            # Generate SQL using Groq
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1
            )
            
            generated_sql = chat_completion.choices[0].message.content.strip()
            
            # Clean up the SQL (remove markdown if present)
            if "```sql" in generated_sql:
                generated_sql = generated_sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in generated_sql:
                generated_sql = generated_sql.split("```")[1].split("```")[0].strip()
            
            print(f"-> Generated SQL: {generated_sql}")
            
            # Execute SQL with connection pooling
            with self.engine.begin() as conn:  # Using begin() for automatic transaction management
                result = conn.execute(text(generated_sql))
                
                # For SELECT queries, return the results
                if generated_sql.strip().lower().startswith('select'):
                    results_as_dicts = [dict(row._mapping) for row in result]
                    print(f"-> SQL executed successfully. Found {len(results_as_dicts)} rows.")
                    return results_as_dicts
                # For INSERT/UPDATE/DELETE queries, return affected rows
                else:
                    return [{"message": "Operation completed successfully", "rows_affected": result.rowcount}]
        
        except Exception as e:
            print(f"!!! Error during SQL generation or execution: {e}")
            return [{"error": "Failed to process SQL query.", "details": str(e)}]
    
    def _format_schema_for_llm(self) -> str:
        """Format database schema for LLM consumption"""
        if not self.db_schema or "schema" not in self.db_schema:
            return "No schema available"
        
        schema_text = "Database Schema:\n"
        for table_name, table_info in self.db_schema["schema"].items():
            schema_text += f"\nTable: {table_name}\n"
            schema_text += "Columns:\n"
            for col in table_info.get("columns", []):
                schema_text += f"  - {col['name']} ({col['type']})\n"
            
            if table_info.get("foreign_keys"):
                schema_text += "Foreign Keys:\n"
                for fk in table_info["foreign_keys"]:
                    schema_text += f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}\n"
        
        return schema_text
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Main method to process queries with hybrid search capability"""
        start_time = time.time()
        query_type = self.classify_query(query)
        
        try:
            if query_type == "DOCUMENT":
                results = self.search_documents(query)
                return {
                    "query_type": "document",
                    "results": results,
                    "execution_time": time.time() - start_time
                }
            
            elif query_type == "SQL":
                results = self.generate_and_execute_sql(query)
                return {
                    "query_type": "sql",
                    "results": results,
                    "execution_time": time.time() - start_time
                }
            
            elif query_type == "HYBRID":
                # Perform both SQL and document search
                print("Performing hybrid search...")
                
                sql_results = self.generate_and_execute_sql(query)
                doc_results = self.search_documents(query)
                
                # Combine results
                combined_results = {
                    "sql_results": sql_results,
                    "document_results": doc_results,
                    "sql_count": len(sql_results),
                    "document_count": len(doc_results)
                }
                
                return {
                    "query_type": "hybrid",
                    "results": combined_results,
                    "execution_time": time.time() - start_time
                }
            
            else:
                return {
                    "query_type": "unknown",
                    "results": [],
                    "error": "Unknown query type",
                    "execution_time": time.time() - start_time
                }
                
        except Exception as e:
            return {
                "query_type": "error",
                "results": [],
                "error": str(e),
                "execution_time": time.time() - start_time
            }
        