from celery import Celery
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Redis connection details
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Print Redis connection details for debugging
print(f"Celery broker URL: {broker_url}")
print(f"Celery result backend: {result_backend}")

# Create Celery instance
celery = Celery(
    'webreconlite',
    broker=broker_url,
    backend=result_backend
)

# Configure Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Optional: Load tasks module
celery.autodiscover_tasks(['app.tasks'])
