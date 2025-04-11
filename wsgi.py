import os
import sys

# Print current directory and Python path for debugging
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Import the Flask application
from app import create_app

# Create the Flask application instance
print("Creating Flask application...")
app = create_app()
print(f"Flask application created: {app}")

# Run the application if executed directly
if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(host='0.0.0.0', port=8001, debug=True)
