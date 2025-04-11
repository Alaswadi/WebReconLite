from flask import Flask
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-webreconlite')
    app.config['RESULTS_DIR'] = os.path.join(app.root_path, 'results')
    
    # Ensure results directory exists
    os.makedirs(app.config['RESULTS_DIR'], exist_ok=True)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app
