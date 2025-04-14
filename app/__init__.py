from flask import Flask
import os
import sys
from dotenv import load_dotenv

# Print debugging information
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")
print(f"Files in app directory: {os.listdir('./app')}")

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Celery is initialized in celery_app.py

def create_app():
    print("Creating Flask application...")
    app = Flask(__name__)

    # Configure the application
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-webreconlite')
    app.config['RESULTS_DIR'] = os.path.join(app.root_path, 'results')
    app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Configure Celery
    app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    app.config['CELERY_TASK_SERIALIZER'] = 'json'
    app.config['CELERY_RESULT_SERIALIZER'] = 'json'
    app.config['CELERY_ACCEPT_CONTENT'] = ['json']

    print(f"App config: SECRET_KEY={app.config['SECRET_KEY'][:5]}..., DEBUG={app.config['DEBUG']}")

    # Ensure results directory exists
    print(f"Creating results directory: {app.config['RESULTS_DIR']}")
    os.makedirs(app.config['RESULTS_DIR'], exist_ok=True)

    # Initialize database
    print("Initializing database...")
    from app.database import init_db
    if init_db():
        print("Database initialized successfully")
    else:
        print("Failed to initialize database")

    # Register blueprints
    print("Registering blueprints...")
    from app.routes import main
    app.register_blueprint(main)
    print("Blueprints registered successfully")

    @app.route('/debug')
    def debug():
        return {
            'python_version': sys.version,
            'current_directory': os.getcwd(),
            'environment': dict(os.environ),
            'app_config': {
                'DEBUG': app.config['DEBUG'],
                'RESULTS_DIR': app.config['RESULTS_DIR'],
                'SECRET_KEY': app.config['SECRET_KEY'][:5] + '...',
            }
        }

    # Celery is initialized in celery_app.py
    # We'll set up Flask app context for Celery tasks in celery_worker.py

    print("Flask application created successfully")
    return app
