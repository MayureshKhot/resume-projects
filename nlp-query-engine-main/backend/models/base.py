from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    
    emp_id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    dept_id = Column(Integer, ForeignKey('departments.dept_id'))
    salary = Column(Integer)
    
    department = relationship("Department", back_populates="employees")
    documents = relationship("Document", back_populates="employee")

class Department(Base):
    __tablename__ = 'departments'
    
    dept_id = Column(Integer, primary_key=True)
    dept_name = Column(String(50), nullable=False)
    employees = relationship("Employee", back_populates="department")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # e.g., 'resume', 'general'
    emp_id = Column(Integer, ForeignKey('employees.emp_id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    employee = relationship("Employee", back_populates="documents")