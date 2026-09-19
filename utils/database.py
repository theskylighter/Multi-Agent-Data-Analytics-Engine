import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class DatabaseUtil:

    def __init__(self, db_url: str):
        """
        Accepts a single DATABASE_URL string (perfect for Neon DB)
        """
        self.db_url = db_url

    def _get_connection(self):
        """
        Helper method to create a fresh connection when needed.
        Serverless databases like Neon dynamically close idle connections,
        so creating a connection per operation prevents 'connection dead' crashes.
        """
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            return None

    def schema_details(self, schema_name: str):
        schema_info_context = f"Database Schema: {schema_name}\n"
        
        connection = self._get_connection()
        if not connection:
            return "Failed to establish a database connection."

        cursor = connection.cursor()

        try: 
            # Fetch tables safely using a parameterized query
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s;", 
                (schema_name,)
            )
            tables_list = cursor.fetchall()

            for table in tables_list:
                table_name = table[0]
                schema_info_context += f"\nTable: {table_name}\n"

                # Adding Columns & Data Types (Filtered by schema to avoid naming conflicts)
                cursor.execute(
                    """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s;
                    """, 
                    (schema_name, table_name)
                )
                columns_list = cursor.fetchall()

                for column in columns_list:
                    column_name = column[0]
                    data_type = column[1]
                    schema_info_context += f"  Column: {column_name}, Data Type: {data_type}\n"

                    #schema_info_context = "Database Schema: public

                    # Table: users
                    #   Column: user_id, Data Type: INTEGER
                    #   Column: first_name, Data Type: VARCHAR"

                # Adding Sample Data (Safely formatted schema and table identifiers)
                from psycopg2 import sql
                
                sample_query = sql.SQL("SELECT * FROM {}.{} LIMIT 5;").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)
                )
                cursor.execute(sample_query)
                sample_data = cursor.fetchall()
                
                schema_info_context += "  Sample Data:\n"
                for row in sample_data:
                    schema_info_context += f"    {row}\n"
                # Database Schema: public

                # Table: users
                #   Column: user_id, Data Type: INTEGER
                #   Column: first_name, Data Type: VARCHAR
                #   Sample Data:
                #     (1, 'Alice')
                #     (2, 'Bob')

        except Exception as e:
            print(f"Error fetching schema details: {e}")
            schema_info_context += f"Error fetching schema details: {e}"

        finally:
            # Safely cleaning up resources
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        
        return schema_info_context

    def execute_sql(self, query: str):
        connection = self._get_connection()
        if not connection:
            return None
            
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            
            # Fetch if the query returns rows (e.g. SELECT)
            if cursor.description:
                result = cursor.fetchall()
            else:
                result = f"Command executed successfully. Rows affected: {cursor.rowcount}"
                
            connection.commit()
            return str(result)
        
        except Exception as e:
            print(f"Error executing query: {e}")
            connection.rollback() # Rollback the failed transaction
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is missing from the environment variables.")
    
    obj = DatabaseUtil(DATABASE_URL)
    result = obj.schema_details("public")
    
    with open("test_schema_details.txt", "w") as f:
        f.write(result)
    
    print("test_schema_details.txt generated successfully!")
