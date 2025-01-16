import os
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App
from dotenv import load_dotenv
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import re

# Load environment variables from .env file
load_dotenv(".env")

# Set Slack API credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  # This is the default and can be omitted
)

# Initialize the Slack app and Slack request handler
app = App(token=SLACK_BOT_TOKEN)
handler = SlackRequestHandler(app)

# Initialize the Flask app
flask_app = Flask(__name__)

# Configure the database URI
db_password = os.getenv("DB_PASS")
flask_app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URI", f"mysql://root:{db_password}@localhost/slackbot"
)
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(flask_app)

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<UserID {self.user_id}, Task {self.task_name!r}, Status {self.status}>'

# Create tables if they don't exist
with flask_app.app_context():
    db.create_all()


def classify_command(input_text, tasks_in_db, user_id):
    system_message = (
        "You are a helpful assistant that classifies task commands. The possible commands are 'add_task', 'update_task', 'view_all_tasks', "
        "'view_task', 'delete_task'. Here are the tasks already in the database: [{tasks_in_db}]. "
        "If the task inputted by the user matches one in the database, modify the task name accordingly. "
        "Based on the user's input, respond with the command followed by the task name, separated by a colon. "
        "For example, if the user's input is 'add the task of writing an email to Emma', the response should be 'add_task:write email to emma'. "
        "If the user's input is 'view status of the task of writing an email to Emma', the response should be 'view_task:write email to emma'. "
        "If the user's input is 'view all of my tasks', the response should be 'view_all_tasks'. "
        "If the user's input is 'delete the task of writing an email to Emma', the response should be 'delete_task:write email to emma'. "
        "If the user's input is 'update the task of writing an email to Emma to 75%', the response should be 'update_task:write email to emma:75'."
    ).format(tasks_in_db=tasks_in_db)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Classify this input into the formatted version: {input_text}"}
            ],
        )

        # Extract and process the response
        
        command_data = response.choices[0].message.content.strip()
        command_parts = command_data.split(':')

        command = command_parts[0].strip()
        task_name = command_parts[1].strip() if len(command_parts) > 1 else None
        task_status = command_parts[2].strip() if len(command_parts) > 2 else None
        
        # Call the appropriate function based on the command
        if command == "add_task":
            return add_task(user_id, task_name)
        elif command == "update_task":
            return update_task(user_id, task_name, task_status)
        elif command == "view_task":
            return view_task(user_id, task_name)
        elif command == "delete_task":
            return delete_task(user_id, task_name)
        elif command == "view_all_tasks":
            return view_all_tasks(user_id)
        else:
            return  f"Unknown command"

    except Exception as e:
        return f"Error processing the command: {str(e)}"


def add_task(user_id, task_name):
    # Check if the task already exists for the user
    with flask_app.app_context():
        existing_task = Task.query.filter_by(user_id=user_id, task_name=task_name).first()
        if existing_task:
            return f"Task '{task_name}' already exists."

        # Create and add a new task
        new_task = Task(user_id=user_id, task_name=task_name, status=0.0)
        db.session.add(new_task)
        db.session.commit()
        return f"Task '{task_name}' added."

# Update task status
def update_task(user_id, task_name, task_status):
    with flask_app.app_context():
        # Find the task for the user
        task = Task.query.filter_by(user_id=user_id, task_name=task_name).first()
        if not task:
            return f"Task '{task_name}' not found."

        # Update task status
        task.status = task_status
        db.session.commit()
        return f"Task '{task_name}' updated to {task_status}%."

# View task
def view_task(user_id, task_name):
    with flask_app.app_context():
        # Find the task for the user
        task = Task.query.filter_by(user_id=user_id, task_name=task_name).first()
        if not task:
            return f"Task '{task_name}' not found."

        return f"Task: '{task_name}' with status {task.status}%."

# Delete task
def delete_task(user_id, task_name):
    with flask_app.app_context():
        # Find the task for the user
        task = Task.query.filter_by(user_id=user_id, task_name=task_name).first()
        if not task:
            return f"Task '{task_name}' not found."

        # Delete the task
        db.session.delete(task)
        db.session.commit()
        return f"Task '{task_name}' deleted."

# View all tasks for a user

def view_all_tasks(user_id):
    with flask_app.app_context():
        tasks = Task.query.filter_by(user_id=user_id).all()
        if not tasks:
            return f"No tasks found."

        task_list = "\n".join([f"Task: {task.task_name}, Status: {task.status}%" for task in tasks])
        return f"All tasks:\n{task_list}"



@app.event("app_mention")
def handle_mentions(body, say):
    """
    Event listener for mentions in Slack.
    When the bot is mentioned, this function processes the text and sends a response.
    """
    user_id = body["event"]["user"]

    # Use application context to interact with the database
    with flask_app.app_context():
        # Query all tasks for the user
        tasks_in_db = Task.query.filter_by(user_id=user_id).all()

    # Format the task names as a string
    task_names = ', '.join([task.task_name.lower() for task in tasks_in_db])

    text = body["event"]["text"]
    
    # Remove mention and extra spaces
    cleaned_text = re.sub(r'<@[\w]+>', '', text).strip()

    # Pass the cleaned-up text and task names to classify_command
    response = classify_command(cleaned_text, task_names, user_id)

    say(response)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Route for handling Slack events.
    This function passes the incoming HTTP request to the SlackRequestHandler for processing.
    """
    return handler.handle(request)

# Run the Flask app
if __name__ == "__main__":
    flask_app.run()

