from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sql_database_handler import MysqlConnectionManager as ConnectionManager
import logging, traceback
from encryption_decryption import EncryptionDecryption

# Initialize the Flask application
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize the JWT manager
jwt = JWTManager(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') #, filename='app.log', filemode='a')

# Global variables
users_table_name = app.config['USERS_TABLE']
tasks_table_name = app.config['TASKS_TABLE']
secret_key = app.config['SECRET_KEY']

# Utility function to handle database connection and query execution
def get_db_manager():
    return ConnectionManager(app.config['DB_HOST'], app.config['DB_PORT'], app.config['DB_NAME'], 
                             app.config['MYSQL_USERNAME'], app.config['MYSQL_PASSWORD'])

def get_user_data_for_username(username):
    db_manager = get_db_manager()
    return db_manager.getData(users_table_name, [], json_where_clause=f" username = '{username}' ", logger=logging)

def get_user_data_for_email(email):
    db_manager = get_db_manager()
    return db_manager.getData(users_table_name, [], json_where_clause=f" email = '{email}'", logger=logging)


@app.route('/', methods=['GET'])
def base_page():
    logging.debug("Visiting the login page")
    return render_template('home.html')

@app.route('/signup', methods=['GET'])
def signup_page():
    logging.debug("Visiting the signup page")
    return render_template('signup.html')

@app.route('/login', methods=['GET'])
def login_page():
    logging.debug("Visiting the login page")
    return render_template('login.html')

@app.route('/home', methods=['GET'])
def home_page():
    logging.debug("Visiting the home page")
    return render_template('home.html')

# Route for User Registration (Sign Up)
@app.route('/signup', methods=['POST'])
def signup():
    try:
        input_data = request.get_json()
        username = input_data.get('username', '')
        password = input_data.get('password', '')
        email = input_data.get('email', '')

        # Check if username already exists
        user_data = get_user_data_for_username(username)
        if len(user_data) > 0:
            logging.error("Signup failed: Username already exists.")
            return jsonify(message="Username already exists"), 400
        
        # Check if email already exists
        email_data = get_user_data_for_email(email)
        if len(email_data) > 0:
            logging.error("Signup failed: email already exists.")
            return jsonify(message="Email already exists"), 400

        # Encrypt the password
        encryption_decryption = EncryptionDecryption(secret_key)
        encrypted_password = encryption_decryption.encrypt_data(password)

        # Insert the new user into the database
        db_manager = get_db_manager()
        jsonObjData = {"username": username, "email": email, "password": encrypted_password}
        user_id = db_manager.insertData(users_table_name, jsonObjData, logger=logging)
        
        if not user_id:
            logging.error("Signup failed for user: %s, email: %s", username, email)
            return jsonify(message="Something went wrong"), 401

        logging.info("User successfully registered: %s", username)
        return jsonify(message="User registered successfully"), 201

    except Exception as e:
        traceback.print_exc()
        logging.error(f"Signup failed for user: {username}, email: {email}")
        logging.error(f"Error: {str(e)}")
        return jsonify(message="Something went wrong"), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data.get('username', '')
    password = data.get('password', '')

    # Fetch user data from the database
    user_data = get_user_data_for_username(username_or_email)
    email_data = get_user_data_for_email(username_or_email)
    if len(user_data) == 0 and len(email_data) == 0:
        logging.error("Login failed for user: %s, invalid credentials", username_or_email)
        return jsonify(message="Invalid credentials"), 401
    username = username_or_email
    if len(user_data) == 0:
        user_data = email_data
        username = user_data[0]["username"]

    encryption_decryption = EncryptionDecryption(secret_key)
    if encryption_decryption.decrypt_data(user_data[0]["password"]) == password:
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        logging.error("Login failed for user: %s, invalid credentials", username_or_email)
        return jsonify(message="Invalid credentials"), 401

@app.route('/tasks', methods=['GET', 'POST'])
@jwt_required()
def manage_tasks():
    current_user = get_jwt_identity()
    db_manager = get_db_manager()
    # Get user ID
    user_data = db_manager.getData(users_table_name, [], json_where_clause=f" username ='{current_user}'", logger=logging)
    user_id = user_data[0]["id"]

    if request.method == 'GET':
        tasks_data = db_manager.getData(tasks_table_name, [], json_where_clause=f" user_id ='{user_id}'", logger=logging)
        return jsonify(tasks_data)

    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        description = data.get('description', '')

        # Insert new task into the database
        task_data = db_manager.insertData(tasks_table_name, {"title": title, "description": description, "user_id": user_id}, logger=logging)
        logging.info("Task added by %s: %s", current_user, title)
        return jsonify(message="Task added successfully"), 201

@app.route('/tasks/<task_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def task_operations(task_id):
    current_user = get_jwt_identity()
    db_manager = get_db_manager()

    # Get user ID and task details
    user_data = db_manager.getData(users_table_name, [], json_where_clause=f" username ='{current_user}'", logger=logging)
    user_id = user_data[0]["id"]
    tasks_data = db_manager.getData(tasks_table_name, [], json_where_clause=f" id ='{task_id}'", logger=logging)

    if not tasks_data or tasks_data[0]["user_id"] != user_id:
        return jsonify(message="Task not found or permission denied"), 404

    if request.method == 'PUT':
        data = request.get_json()
        title = data.get('title', tasks_data[0]["title"])
        description = data.get('description', tasks_data[0]["description"])
        completed = data.get('completed', tasks_data[0]["completed"])

        # Update task details in the database
        col_values = {"title": title, "description": description, "completed": completed}
        updated = db_manager.updateData(tasks_table_name, col_values, f"id = {task_id}", logger=logging)

        if updated:
            logging.info("Task updated by %s: %s", current_user, tasks_data[0]["title"])
            return jsonify(message="Task updated successfully"), 200
        else:
            logging.error("Could not update task for %s: %s", current_user, tasks_data[0]["title"])
            return jsonify(message="Internal server error"), 500

    if request.method == 'DELETE':
        deleted = db_manager.deleteData(tasks_table_name, f" id ='{task_id}'", logger=logging)
        if deleted:
            logging.info("Task deleted by %s: %s", current_user, tasks_data[0]["title"])
            return jsonify(message="Task deleted successfully"), 200
        else:
            logging.error("Could not delete task for %s: %s", current_user, tasks_data[0]["title"])
            return jsonify(message="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True, port=8010)
