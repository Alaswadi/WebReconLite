from flask import Flask, jsonify
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

    @app.route('/db-status')
    def db_status():
        """Check the status of the database."""
        import sqlite3
        from app.database import DB_FILE, get_db_connection

        # Check if the database file exists
        db_exists = os.path.exists(DB_FILE)

        # Try to connect to the database
        conn = get_db_connection()
        connection_successful = conn is not None

        # Get table counts
        table_counts = {}
        if connection_successful:
            try:
                cursor = conn.cursor()

                # Get list of tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row['name'] for row in cursor.fetchall()]

                # Get count for each table
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]

                # Close the connection
                conn.close()
            except Exception as e:
                table_counts['error'] = str(e)

        return jsonify({
            'db_file': DB_FILE,
            'db_exists': db_exists,
            'connection_successful': connection_successful,
            'table_counts': table_counts
        })

    # Celery is initialized in celery_app.py
    # We'll set up Flask app context for Celery tasks in celery_worker.py

    print("Flask application created successfully")
    return app
