import re
import logging
from openai_agent import OpenAIAgent
from connectors.snowflake_connector import SnowflakeConnector
from logging_config import setup_logging

# Set up logging
setup_logging()

class QueryService:
    def __init__(self):
        self.openai_agent = OpenAIAgent()
        self.snowflake_agent = SnowflakeConnector()

    def process_query(self, user_query, sql_in_answer=False, sql_mode=False):
        try:
            if sql_mode:
                # In SQL mode, use the user query directly
                refined_query = user_query
                if not self._is_select_query(refined_query):
                    raise ValueError("Only SELECT queries are allowed.")
                logging.info("SQL mode enabled. Using direct query.")
            else:
                if self._is_query(user_query):
                    raise ValueError("Only language text is allowed. To use SQL queries, enable SQL mode in Options.")
                # Translate user query into SQL query
                openai_message_response = self.openai_agent.create_message(user_query)
                if openai_message_response["Error"]:
                    return openai_message_response

                self.openai_agent.execute_run()
                openai_retrieval_response = self.openai_agent.retrieve_messages()
                if openai_retrieval_response["Error"]:
                    return openai_retrieval_response

                logging.info(f"Response from OpenAI: {openai_retrieval_response}")

                # Extract query from OpenAI response
                refined_query = self._extract_query(openai_retrieval_response["Data"])
                logging.info(f"Refined query: {refined_query}")

            # Execute the query
            if refined_query is not None:
                snowflake_response = self.snowflake_agent.execute_query(refined_query)
                logging.info("Query executed on Snowflake.")
                response_data = {
                    "snowflake_response": snowflake_response.get("Data"),
                    "openai_query": refined_query if sql_in_answer else None
                }
                return {"Data": response_data, "Error": snowflake_response.get("Error")}
            else:
                message = "No valid SQL query provided."
                logging.error(message)
                return {"Data": None, "Error": message}

        except Exception as e:
            logging.error(f"Error in process_query: {e}")
            return {"Data": None, "Error": str(e)}
    
    def _extract_query(self, openai_response):
        query = openai_response.replace("\n", " ").replace("`", "")
        print("Original Response:", query)

        # Check for both 'WITH' and 'SELECT' keywords
        if "WITH" in query or "SELECT" in query:
            with_position = query.find("WITH")
            select_position = query.find("SELECT")

            # Determine the starting position of the actual query
            start_position = min(with_position if with_position != -1 else len(query),
                                 select_position if select_position != -1 else len(query))

            # Find the end of the query marked by a semicolon
            end_select_position = query.find(";", start_position)
            if end_select_position != -1:
                query = query[start_position:end_select_position + 1]
            else:
                query = query[start_position:]
            print("Extracted Query:", query)
        else:
            query = None

        return query
    
    def _is_query(self, query):
        pattern = r"^(SELECT|INSERT INTO|UPDATE|DELETE FROM)\b"
        return re.match(pattern, query.strip(), re.IGNORECASE) is not None

    def _is_select_query(self, query):
        normalized_query = query.lower().strip()
        # Check if the query starts with 'select'
        return normalized_query.startswith("select")

    def _close_services(self):
        # Close connections of snowflake_agent
        self.snowflake_agent.close_connection()
        logging.info("Snowflake connection closed.")

