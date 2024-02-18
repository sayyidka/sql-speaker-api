import time
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from logging_config import setup_logging

# Set up logging
setup_logging()

class OpenAIAgent:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        openai_key = os.getenv("OPENAI_KEY")
        assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
        self.thread_id = os.getenv("OPENAI_THREAD_ID")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=openai_key)

        # Get assistant
        self.my_assistant = self.client.beta.assistants.retrieve(assistant_id)

    def create_message(self, content):
        try:
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=content
            )
            return {"Data": message, "Error": None}
        except Exception as e:
            logging.error(f"Error creating OpenAI message: {e}")
            return {"Data": None, "Error": str(e)}

    def execute_run(self):
        try:
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.my_assistant.id,
                tools=[{"type": "retrieval"}]
            )

            while run.status != "completed":
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                if run.status in ["queued", "in_progress"]:
                    logging.info(f"Run {run.status}...")
                    time.sleep(2)
                    continue
                elif run.status in ["cancelling", "cancelled", "failed", "expired"]:
                    logging.error("Error in Run")
                    return {"Data": None, "Error": "Run failed or was cancelled"}
                logging.info(run.status)

            return {"Data": "Run completed", "Error": None}
        except Exception as e:
            logging.error(f"Error executing OpenAI run: {e}")
            return {"Data": None, "Error": str(e)}

    def retrieve_messages(self):
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread_id
            )
            return {"Data": messages.data[0].content[0].text.value, "Error": None}
        except Exception as e:
            logging.error(f"Error retrieving messages from OpenAI: {e}")
            return {"Data": None, "Error": str(e)}

