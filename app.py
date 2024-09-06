from flask import Flask, jsonify, request, render_template
import os
import json

app = Flask(__name__)

# Path to store the user data (unique IDs with names)
ID_FILE_PATH = os.path.join(os.path.dirname(__file__), 'user_data.json')

# Function to retrieve the unique ID of the current device
def get_unique_id():
    try:
        # Use a command based on the OS to get some unique detail
        if os.name == 'nt':  # Windows
            command = "wmic csproduct get uuid"  # This gets a unique hardware UUID
        else:  # Linux or macOS
            command = "uname -r"  # Kernel version as an example
        result = os.popen(command).read().strip()
        return result
    except Exception as e:
        return None

# Function to store the unique ID with the username in a JSON file
def store_id(username, unique_id):
    try:
        user_data = {}
        # Load existing data if it exists
        if os.path.exists(ID_FILE_PATH):
            with open(ID_FILE_PATH, 'r') as file:
                user_data = json.load(file)

        # Store or update the user's unique ID
        user_data[username] = unique_id

        # Write back to the file
        with open(ID_FILE_PATH, 'w') as file:
            json.dump(user_data, file)
    except Exception as e:
        print(f"Error storing unique ID: {e}")

# Function to load the stored unique ID for a given username
def load_stored_id(username):
    try:
        if os.path.exists(ID_FILE_PATH):
            with open(ID_FILE_PATH, 'r') as file:
                user_data = json.load(file)
                return user_data.get(username)  # Return unique ID for the username
        else:
            return None
    except Exception as e:
        return None

# Function to check if a unique ID is already associated with another username
def is_id_already_taken(unique_id):
    try:
        if os.path.exists(ID_FILE_PATH):
            with open(ID_FILE_PATH, 'r') as file:
                user_data = json.load(file)
                for user, stored_id in user_data.items():
                    if stored_id == unique_id:
                        return user  # Return the username that already has this ID
        return None
    except Exception as e:
        return None

@app.route('/')
def home():
    # Serve the HTML file (UI for login)
    return render_template('index.html')

@app.route('/validate_user', methods=['POST'])
def validate_user():
    username = request.form.get('username')

    if not username:
        return jsonify({"error": "Username is required."}), 400

    current_id = get_unique_id()
    if not current_id:
        return jsonify({"error": "Unable to retrieve current unique ID."}), 500

    # Check if the current unique ID is already stored for another user
    existing_user = is_id_already_taken(current_id)
    if existing_user and existing_user != username:
        # Deny access if the ID is already taken by another user
        return jsonify({"error": f"Access denied. This device is already registered with another user: {existing_user}."}), 403

    stored_id = load_stored_id(username)

    if stored_id is None:
        # No ID stored for this user, so store the current ID
        store_id(username, current_id)
        return jsonify({"message": f"New user {username}. Unique ID has been stored."}), 200
    elif stored_id == current_id:
        # ID matches for the user
        return jsonify({"message": f"Access granted for {username}. Unique ID matches."}), 200
    else:
        # ID does not match
        return jsonify({"error": f"Access denied for {username}. Please use your registered device."}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
