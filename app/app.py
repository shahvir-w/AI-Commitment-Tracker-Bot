import os
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App
from flask import Flask, request
from openai import OpenAI
from app.models import db
from app.config import SLACK_BOT_TOKEN, DB_PASSWORD, OPENAI_API_KEY
from app.slack_events import handle_mentions, handle_joined

# Initialize the Flask app
flask_app = Flask(__name__)
flask_app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URI", f"mysql://root:{DB_PASSWORD}@localhost/slackbot"
)
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(flask_app)

# Initialize the Slack app and Slack request handler
app = App(token=SLACK_BOT_TOKEN)
handler = SlackRequestHandler(app)

client = OpenAI(api_key=OPENAI_API_KEY)

@app.event("member_joined_channel")
def handle_member_joined(body, say):
    handle_joined(body, say)

@app.event("app_mention")
def handle_mention_event(body, say):
    handle_mentions(body, say, flask_app, client)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Route for handling Slack events.
    """
    return handler.handle(request)

# Run the Flask app
if __name__ == "__main__":
    flask_app.run()
