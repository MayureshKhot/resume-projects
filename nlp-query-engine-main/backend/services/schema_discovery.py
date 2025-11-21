from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

class SchemaDiscovery():
    def analyze_database(self, connection_string:str):
        try:
            engine = create_engine(connection_string)
            inspector = inspect(engine) #look at the tables and stuff
            
            table_names = inspector.get_table_names()
            print(f"Found tables: {table_names}")
            final_schema = {}
            
            for table_name in table_names:
                print(f"--- processing table: {table_name} ---")
                columns_from_inspector = inspector.get_columns(table_name)
                
                my_columns_list = []
                for col in columns_from_inspector:
                    my_columns_list.append({
                        "name":col['name'],
                        "type": str(col['type'])
                    })
            
                fks_from_inspector = inspector.get_foreign_keys(table_name)
                my_fks_list = []
                for fk in fks_from_inspector:
                    my_fks_list.append({
                        "constrained_columns": fk['constrained_columns'],
                        "referred_table": fk['referred_table'],
                        "referred_columns": fk['referred_columns']
                    })
                
                final_schema[table_name] = {
                    "columns": my_columns_list,
                    "foreign_keys": my_fks_list
                }
                
            return {"schema": final_schema}
    
        except Exception as e:
            print(f"!!! AN ERROR OCCURRED: {e}")
            return {"error": "Something went wrong, check the connection string."}
    
    def _infer_table_purpose(self, shema:dict) -> dict:
        pass