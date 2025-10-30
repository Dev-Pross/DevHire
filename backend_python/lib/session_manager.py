import json
import os

class SessionManager:
    def __init__(self, session_file='session.json'):
        self.session_file = session_file
        self.logged_in_context = None

    def save_session(self, context):
        """Save the logged in context to a file."""
        self.logged_in_context = context
        with open(self.session_file, 'w') as file:
            json.dump(context, file)

    def load_session(self):
        """Load the logged in context from a file."""
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as file:
                self.logged_in_context = json.load(file)
        else:
            raise FileNotFoundError("Session file not found.")

    def get_logged_in_context(self):
        """Get the current logged in context."""
        return self.logged_in_context
