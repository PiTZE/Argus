import yaml
import bcrypt
import os

CONFIG_FILE = 'config.yaml'

def load_config():
    """Loads the config.yaml file."""
    if not os.path.exists(CONFIG_FILE):
        return {
            'cookie': {
                'expiry_days': 1,
                'key': 'super_secret_cookie_key', # IMPORTANT: Change this to a strong, random key!
                'name': 'streamlit_app_cookie'
            },
            'credentials': {
                'usernames': {}
            }
        }
    with open(CONFIG_FILE, 'r') as file:
        return yaml.safe_load(file)

def save_config(config):
    """Saves the updated config to config.yaml."""
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config, file, sort_keys=False, default_flow_style=False)
    print(f"Configuration saved to {CONFIG_FILE}")

def hash_password(password):
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def add_user(username, password, name, email):
    """Adds a new user to the configuration."""
    config = load_config()
    if username in config['credentials']['usernames']:
        print(f"Error: User '{username}' already exists.")
        return

    hashed_pw = hash_password(password)
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hashed_pw
    }
    save_config(config)
    print(f"User '{username}' added successfully.")

def remove_user(username):
    """Removes an existing user from the configuration."""
    config = load_config()
    if username not in config['credentials']['usernames']:
        print(f"Error: User '{username}' not found.")
        return

    del config['credentials']['usernames'][username]
    save_config(config)
    print(f"User '{username}' removed successfully.")

def list_users():
    """Lists all users in the configuration."""
    config = load_config()
    users = config['credentials']['usernames']
    if not users:
        print("No users found.")
        return

    print("\n--- Existing Users ---")
    for username, details in users.items():
        print(f"Username: {username}")
        print(f"  Name: {details.get('name', 'N/A')}")
        print(f"  Email: {details.get('email', 'N/A')}")
        print("-" * 20)
    print("----------------------\n")


def main():
    """Main function for the CLI user manager."""
    while True:
        print("\n--- User Manager Menu ---")
        print("1. Add User")
        print("2. Remove User")
        print("3. List Users")
        print("4. Hash a Password (for manual entry)")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter new username: ")
            password = input("Enter password for new user: ")
            name = input("Enter full name for new user: ")
            email = input("Enter email for new user: ")
            add_user(username, password, name, email)
        elif choice == '2':
            username = input("Enter username to remove: ")
            remove_user(username)
        elif choice == '3':
            list_users()
        elif choice == '4':
            password_to_hash = input("Enter password to hash: ")
            hashed = hash_password(password_to_hash)
            print(f"Hashed password: {hashed}")
            print("Copy this into your config.yaml manually if needed.")
        elif choice == '5':
            print("Exiting User Manager.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()