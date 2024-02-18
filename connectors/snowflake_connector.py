import os
import logging
import snowflake.connector
from snowflake.connector import ProgrammingError
from dotenv import load_dotenv
from logging_config import setup_logging

# Set up logging
setup_logging()

class SnowflakeConnector:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        self.account = os.getenv('SNOWFLAKE_ACCOUNT')
        self.username = os.getenv('SNOWFLAKE_USERNAME')
        self.password = os.getenv('SNOWFLAKE_PWD')
        self.warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
        self.database = os.getenv('SNOWFLAKE_DATABASE')

        # Initialize connection
        self.conn = snowflake.connector.connect(
            user=self.username,
            password=self.password,
            account=self.account,
            warehouse=self.warehouse,
            database=self.database
        )
        self.cursor = self.conn.cursor()

    def execute_query(self, query):
        response = {"Error": None, "Data": None}
        try:
            self.cursor.execute(query)
            logging.info("Query executed successfully in Snowflake.")

            column_names = [desc[0] for desc in self.cursor.description]
            results = self.cursor.fetchall()

            response["Data"] = {
                "columns": column_names,
                "rows": results
            }
        except ProgrammingError as pe:
            logging.error(f"ProgrammingError in Snowflake query: {pe}")
            response["Error"] = f"ProgrammingError: {pe}"
        except Exception as e:
            logging.error(f"Error in Snowflake query execution: {e}")
            response["Error"] = f"General Error: {e}"
        finally:
            self.cursor.close()
        return response

    def close_connection(self):
        # Close the connection
        self.conn.close()

