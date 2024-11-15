import os
import uuid
import json
import datetime
import requests
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Add the parent directory to sys.path để import được config.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import config  # Now we can import config from the parent directory


# Import ChatAssistant from class 1
# Assuming your class 1 code is saved in 'chat_assistant.py'
from ChatAssistant_class import ChatAssistant  # Adjust the import path as needed

class ExtendedChatAssistant(ChatAssistant):
    """
    An extended version of ChatAssistant that includes conversation management and logging to Lark Base.
    """

    def __init__(self, api_url, api_key, lark_app_token, lark_table_id, lark_bearer_access_token):
        super().__init__(api_url, api_key)
        self.current_conversation_id = None
        self.lark_app_token = lark_app_token
        self.lark_table_id = lark_table_id
        self.lark_bearer_access_token = lark_bearer_access_token
        self.lark_url = (
            f"https://open.larksuite.com/open-apis/bitable/v1/apps/"
            f"{self.lark_app_token}/tables/{self.lark_table_id}/records"
        )

    def start_new_conversation(self):
        """
        Start a new conversation by resetting the conversation ID and chat history.
        """
        self.current_conversation_id = str(uuid.uuid4())
        self.chat_history = []

    def chat(self, user_input_prompt):
        """
        Send a user prompt to the assistant, receive a response, and log the interaction.

        Args:
            user_input_prompt (str): The user's input question.

        Returns:
            str: The assistant's response.
        """
        if not self.current_conversation_id:
            self.start_new_conversation()
        response_content = super().chat(user_input_prompt)
        self._log_to_larkbase(user_input_prompt, response_content)
        return response_content

    def _log_to_larkbase(self, user_input, assistant_response):
        """
        Log the chat interaction to Lark Base.

        Args:
            user_input (str): The user's input question.
            assistant_response (str): The assistant's response.
        """
        payload = {
            "fields": {
                "system_prompt": (
                    "You are a friendly and helpful assistant for CSKH-StepUpEducation. "
                    "Your responses should be natural, engaging, and conversational. "
                    "Use the knowledge base content to inform your answers, but present "
                    "the information in a smooth, chatbot-like manner. If the knowledge base "
                    "doesn't contain relevant information, politely inform the user."
                ),
                "conversation_id": self.current_conversation_id,
                "chat_id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "user_input": user_input,
                "assistant_response": assistant_response,
            }
        }

        headers = {
            'Authorization': f'Bearer {self.lark_bearer_access_token}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                self.lark_url, headers=headers, data=json.dumps(payload)
            )
            response.raise_for_status()
            print("Log entry inserted successfully")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while logging to Lark Base: {e}")

# Example usage
if __name__ == "__main__":
    # Get configurations from environment variables
    API_URL = os.getenv('API_URL')
    API_KEY = os.getenv('API_KEY')
    LARK_APP_TOKEN = config.APP_BASE_TOKEN
    LARK_TABLE_ID = config.BASE_TABLE_ID
    LARK_BEARER_ACCESS_TOKEN = os.getenv('LARK_BEARER_ACCESS_TOKEN')

    if not API_URL or not API_KEY:
        print("Error: API_URL or API_KEY not found in environment variables")
    elif not LARK_APP_TOKEN or not LARK_TABLE_ID or not LARK_BEARER_ACCESS_TOKEN:
        print("Error: Lark configurations not found in environment variables")
    else:
        assistant = ExtendedChatAssistant(
            API_URL,
            API_KEY,
            LARK_APP_TOKEN,
            LARK_TABLE_ID,
            LARK_BEARER_ACCESS_TOKEN,
        )
        while True:
            prompt = input(
                "Enter your question (or type 'exit' to quit, 'new' to start a new conversation): "
            )
            if prompt.lower() == 'exit':
                break
            elif prompt.lower() == 'new':
                assistant.start_new_conversation()
                print("New conversation started.")
                continue
            result = assistant.chat(prompt)
            print(result)
