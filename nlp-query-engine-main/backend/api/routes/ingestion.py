from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import List
from pydantic import BaseModel
from services.simple_document_processor import SimpleDocumentProcessor as DocumentProcessor
from services.schema_discovery import SchemaDiscovery
from core.config import settings
from sqlalchemy.orm import sessionmaker
from models.base import Document
import os

router = APIRouter()

print("Initializing ingestion router")

class DatabaseConnectionRequest(BaseModel):
    connection_string: str

@router.post("/connect-database")
async def connect_database(request: DatabaseConnectionRequest):
    """
    Connect to database and discover schema
    """
    try:
        discoverer = SchemaDiscovery()
        schema = discoverer.analyze_database(request.connection_string)
        
        if "error" in schema:
            raise HTTPException(status_code=400, detail=schema["error"])
        
        # Store connection info globally (in production, use proper state management)
        from main import set_database_connection
        set_database_connection(request.connection_string, schema)
        
        return {
            "message": "Database connected successfully",
            "schema": schema,
            "tables_count": len(schema.get("schema", {}))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Form

from models.base import Employee

@router.post("/upload-documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    emp_id: str = Form(..., description="Employee ID to associate the documents with")
):
    """
    Upload and process documents for semantic search
    """
    print(f"\n=== Document Upload Request ===")
    print(f"Employee ID input: {emp_id}")
    
    # Convert employee ID to integer
    try:
        emp_id_int = int(emp_id)
        print(f"Converted Employee ID: {emp_id_int}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Employee ID must be a valid number")
        
    print(f"Number of files: {len(files) if files else 0}")
    if files:
        print("Files:")
        for file in files:
            print(f"- {file.filename} (size: {file.size} bytes, content_type: {file.content_type})")
    
    try:
        # Get document processor from main
        from main import get_document_processor
        processor = get_document_processor()
        
        if not processor:
            raise HTTPException(status_code=500, detail="Document processor not initialized")
        
        # Validate employee exists
        session = processor.Session()
        try:
            employee = session.query(Employee).filter_by(emp_id=emp_id_int).first()
            if not employee:
                # Log available employee IDs for debugging
                available_ids = [e.emp_id for e in session.query(Employee).all()]
                print(f"Available employee IDs in database: {available_ids}")
                raise HTTPException(status_code=404, 
                    detail=f"Employee with ID {emp_id_int} not found. Available IDs: {available_ids}")
        finally:
            session.close()
            
        # Validate file types and sizes
        for file in files:
            if not any(file.filename.lower().endswith(ext) for ext in settings.SUPPORTED_FORMATS):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file.filename}. Supported formats: {settings.SUPPORTED_FORMATS}"
                )
            
            # Check file size
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
                )
        
        # Get document processor from main
        from main import get_document_processor
        processor = get_document_processor()
        
        if not processor:
            raise HTTPException(status_code=500, detail="Document processor not initialized")
        
        # Process files
        processed_content = await processor.process_files(files, emp_id_int)
        
        # Documents are automatically stored in the database
        print(f"Processed {len(processed_content)} documents")
        print(f"Document store now has {processor.get_document_count()} documents with employee ID {emp_id_int}")
        
        # Get employee details for the response
        session = processor.Session()
        try:
            employee = session.query(Employee).filter_by(emp_id=emp_id_int).first()
            return {
                "message": f"{len(files)} document(s) processed successfully",
                "uploaded_files": [f.filename for f in files],
                "total_documents": len(processed_content),
                "store_count": processor.get_document_count(),
                "employee": {
                    "id": employee.emp_id,
                    "name": employee.full_name,
                    "department": employee.department.dept_name if employee.department else None
                }
            }
        finally:
            session.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents():
    """
    List all uploaded documents
    """
    try:
        from main import get_document_processor
        processor = get_document_processor()
        
        if not processor:
            return {"documents": [], "total_count": 0}
        
        # Create a session
        Session = sessionmaker(bind=processor.engine)
        session = Session()
        
        try:
            # Query all documents
            db_documents = session.query(Document).all()
            
            documents = []
            for doc in db_documents:
                documents.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "content_type": doc.content_type,
                    "size": len(doc.content),
                    "preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat(),
                    "employee": {
                        "id": doc.emp_id,
                        "name": doc.employee.full_name,
                        "department": doc.employee.department.dept_name if doc.employee.department else None
                    } if doc.employee else None
                })
            
            return {
                "documents": documents,
                "total_count": len(documents)
            }
            
        finally:
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees")
async def list_employees():
    """
    List all employees for debugging
    """
    try:
        from main import get_document_processor
        processor = get_document_processor()
        
        if not processor:
            return {"employees": []}
        
        session = processor.Session()
        try:
            employees = session.query(Employee).all()
            return {
                "employees": [
                    {
                        "emp_id": emp.emp_id,
                        "name": emp.full_name,
                        "department": emp.department.dept_name if emp.department else None
                    }
                    for emp in employees
                ]
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Delete a specific document
    """
    try:
        from main import remove_document
        success = remove_document(filename)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": f"Document {filename} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
