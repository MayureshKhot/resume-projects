'''
from sqlalchemy import create_engine, inspect
from core.config import settings

def inspect_database():
    """Utility function to inspect the database structure and content"""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    print(f"\nDatabase Location: {engine.url.database}")
    print("\nTables in database:")
    
    for table_name in inspector.get_table_names():
        print(f"\nTable: {table_name}")
        print("Columns:")
        for column in inspector.get_columns(table_name):
            print(f"  - {column['name']}: {column['type']}")
        
        # Get row count
        result = engine.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = result.scalar()
        print(f"Total rows: {count}")

if __name__ == "__main__":
    inspect_database()
'''
