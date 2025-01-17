from app.models import Task, db

def add_task(user_id, task_name, flask_app):
    with flask_app.app_context():
        existing_task = Task.query.filter_by(user_id=user_id, task_name=task_name).first()
        if existing_task:
            return f"Task '{task_name}' already exists."

        new_task = Task(user_id=user_id, task_name=task_name, status=0.0)
        db.session.add(new_task)
        db.session.commit()
        return f"Task '{task_name}' added."

def update_task(user_id, task_name, task_status, flask_app):
    with flask_app.app_context():
        task = Task.query.filter_by(user_id=user_id, task_name=task_name).first()
        if not task:
            return f"Task '{task_name}' not found."

        task.status = task_status
        db.session.commit()
        return f"Task '{task_name}' updated to {task_status}%."

def view_task(user_id, task_name, flask_app):
    with flask_app.app_context():
        task = Task.query.filter_by(user_id=user_id, task_name=task_name).first()
        if not task:
            return f"Task '{task_name}' not found."
        return f"Task: '{task_name}' with status {task.status}%."

def delete_task(user_id, task_name, flask_app):
    with flask_app.app_context():
        task = Task.query.filter_by(user_id=user_id, task_name=task_name).first()
        if not task:
            return f"Task '{task_name}' not found."

        db.session.delete(task)
        db.session.commit()
        return f"Task '{task_name}' deleted."

def view_all_tasks(user_id, flask_app):
    with flask_app.app_context():
        tasks = Task.query.filter_by(user_id=user_id).all()
        if not tasks:
            return f"No tasks found."

        task_list = "\n".join([f"{index + 1}. *{task.task_name}*, Status: {task.status}%" for index, task in enumerate(tasks)])

        return f"All tasks:\n{task_list}"

def help_message(input_text, client):
    """
    Responds to a user's request for help with instructions on how to use the bot.
    """
    system_message = """
    You are a task management bot named Carl.
    If a user asks for help or seems unsure about how to use the bot, provide them with clear, simple, and concise instructions 
    on how to perform the following commands. Respond in a friendly tone and ensure the user feels supported.

    Instructions:
    1. **Add a Task**: Mention me and say something like:
        - "Add a task to send an email to John."
        - "Add task: Complete the project report."
    2. **View All Tasks**: Mention me and ask:
        - "Show all my tasks."
        - "What tasks do I have?"
    3. **View a Specific Task**: Mention me and say:
        - "View the status of the task to send an email to John."
    4. **Update a Task**: Mention me and ask:
        - "Update the task to send an email to John to 50% complete."
        - "Set the progress of writing the report to 75%."
    5. **Delete a Task**: Mention me and say:
        - "Delete the task to send an email to John."

    Example Response for Help:
    - "You can add, view, update, or delete tasks by mentioning me and describing what you'd like to do. For example:
      - 'Add a task to complete the report.'
      - 'Show me all my tasks.'
      - 'Update the task to send an email to John to 50%.'

      Let me know if you need more detailed help!"

    If the user asks something unrelated to tasks or mentions help in a general way, politely inform them that the bot is primarily designed for task management and provide a brief reminder of its features.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": input_text}
        ],
    )

    return response.choices[0].message.content.strip()
    
    
def more_tasks(input_text, tasks_in_db, client):
    """
    Uses OpenAI API to analyze tasks in the database and provide helpful insights.
    """
    system_message = f"""
    You are a helpful assistant that analyzes a user's tasks and provides insights or support based on the tasks in the database.
    Below is a list of tasks for the user, including their statuses (percentage complete):

    Tasks in Database:
    {tasks_in_db}

    Your goal is to:
    - Analyze the tasks to determine how many tasks there are in total, how many are incomplete (less than 100% status), and how many are complete.
    - Provide insights, such as identifying tasks that are overdue or need attention.
    - Offer helpful suggestions if the user seems overwhelmed, such as prioritizing or breaking large tasks into smaller ones.
    - Respond to the user's input or query in a friendly and concise way. If the input is general, provide a summary of the user's tasks and encourage them to take action.

    Example Inputs and Outputs:
    - Input: "How many tasks do I have?" -> Output: "You have 5 tasks in total: 3 are incomplete, and 2 are complete."
    - Input: "Which tasks are incomplete?" -> Output: "The following tasks are incomplete: 'Write report (status: 50%)', 'Prepare presentation (status: 30%)'."
    - Input: "I'm overwhelmed with my tasks." -> Output: "I see you have 5 tasks in total, with 3 incomplete. I recommend focusing on the most urgent ones, like 'Write report (status: 50%)'."
    """
    try:
        # Send the input and system message to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": input_text},
            ],
        )

        # Extract and return the response content
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error processing the request: {str(e)}"
