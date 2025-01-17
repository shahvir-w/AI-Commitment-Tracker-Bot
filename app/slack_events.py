from app.models import Task
from app.tasks import add_task, update_task, view_task, delete_task, view_all_tasks, help_message, more_tasks
import re

def handle_joined(body, say): 
    """
    Event listener for when bot or a user joins a channel in Slack.
    """
    user_id = body["event"]["user"]
    channel_id = body["event"]["channel"]
    is_bot = body['authorizations'][0].get('is_bot', False)

    # bot joining a channel
    if is_bot:
        say(
            channel=channel_id,
            text=(
                "Hey there, your task tracker Carl has joined! 📝\n\n"
                "If you need help with task tracking, just mention me using '@Carl' and I'll assist you.\n\n"
                "If you're unsure, feel free to ask for help anytime!"
            )
        )
    else:
    # user joining a channel
        say(
            channel=channel_id,
            text=(
                f"Hey <@{user_id}>, welcome to the channel!\n\n"
                "If you need help with task tracking, just mention me using '@Carl' and I'll assist you.\n\n"
                "If you're unsure, feel free to ask for help!"
            )
        )

def handle_mentions(body, say, flask_app, client):
    """
    Event listener for mentions in Slack.
    """
    user_id = body["event"]["user"]

    with flask_app.app_context():
        tasks_in_db = Task.query.filter_by(user_id=user_id).all()

    task_details = ', '.join([f"{task.task_name.lower()} (status: {task.status}%)" for task in tasks_in_db])

    text = body["event"]["text"]
    cleaned_text = re.sub(r'<@[\w]+>', '', text).strip()

    response = classify_command(cleaned_text, task_details, user_id, client, flask_app)
    say(response)

def classify_command(input_text, tasks_in_db, user_id, client, flask_app):
    system_message = f"""
    You are a helpful slack bot for task management. Your goal is to classify task-related commands.
    The user does not type these commands in, rather just says add tasks or show tasks and you need to figure it out.
    
    **Command Options:**
    - 'add_task': Add a new task.
    - 'update_task': Update the status of an existing task.
    - 'delete_task': Delete a specific task.
    - 'view_task': View the status of a specific task.
    - 'view_all_tasks': View all tasks for the user.
    - 'get_help': Understand how to message the bot.
    - 'more_tasks': Addional task analysis, summary, counting, etc.

    **Task Database:**
    The following tasks exist in the database for user: 
    {tasks_in_db}. 
    - If the input refers to a task already in the database, update the task name accordingly.

    **Task Command Format:**
    IMPORTANT: respect the format for commands
    - For 'add_task', the response format is: add_task:<task_name>
    - For 'update_task', the response format is: update_task:<task_name>:<status>
    - For 'view_task', the response format is: view_task:<task_name>
    - For 'delete_task', the response format is: delete_task:<task_name>
    - For 'view_all_tasks', the response is: view_all_tasks
    - For 'get_help': the response is: get_help
    - For 'more_tasks': the response is: more_tasks

    **Example Inputs:**
    - "add task of writing an email to Emma" should be classified as `add_task:write email to emma`.
    - "update the task of writing an email to Emma to 75%" should be classified as `update_task:write email to emma:75`.
    - "view all of my tasks" should be classified as `view_all_tasks`.
    - "delete the task of writing an email to Emma" should be classified as `delete_task:write email to emma`.
    - "hey hows the weather" should be classified as `get_help`.
    - "how do i use this bot" should be classified as `get_help`.
    - "how many tasks do I have" should be classified as `more_tasks`.
    - "summarize my tasks" should be classified as `more_tasks`.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Classify this input into the formatted version: {input_text}"}
            ],
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"Raw Response: {answer}")
        
        command_parts = answer.split(':')
        command = command_parts[0].strip("`").strip().lower()
        task_name = command_parts[1].strip() if len(command_parts) > 1 else None
        task_status = command_parts[2].strip() if len(command_parts) > 2 else None
        
        if command == 'add_task':
            return add_task(user_id, task_name, flask_app)
        elif command == 'update_task':
            return update_task(user_id, task_name, task_status, flask_app)
        elif command == 'view_task':
            return view_task(user_id, task_name, flask_app)
        elif command == 'delete_task':
            return delete_task(user_id, task_name, flask_app)
        elif command == 'view_all_tasks':
            return view_all_tasks(user_id, flask_app)
        elif command == 'get_help':
            return help_message(input_text, client)
        elif command == 'more_tasks':
            return more_tasks(input_text, tasks_in_db, client)
        else:
            return "Sorry I don't understand"
    except Exception as e:
        print( f"Error processing the command: {str(e)}")
        return "Sorry I cannot do that"
