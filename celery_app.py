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
    worker_hijack_root_logger=False,  # Don't hijack the root logger
    worker_redirect_stdouts=False,    # Don't redirect stdout/stderr
    task_always_eager=False,          # Don't run tasks eagerly (synchronously)
    task_acks_late=True,              # Acknowledge tasks after they are executed
    task_track_started=True,          # Track when tasks are started
    task_send_sent_event=True,        # Send events when tasks are sent
    task_ignore_result=False,         # Don't ignore task results
    broker_connection_retry=True,     # Retry broker connection
    broker_connection_max_retries=None,  # Retry broker connection indefinitely
    broker_connection_timeout=10,     # Broker connection timeout
    result_expires=None,              # Results never expire
    worker_prefetch_multiplier=1,     # Prefetch one task at a time
    worker_concurrency=4,             # Number of worker processes
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
)

# Optional: Load tasks module
celery.autodiscover_tasks(['app.tasks'])

# Print Celery configuration for debugging
print("Celery configuration:")
for key, value in celery.conf.items():
    print(f"  {key}: {value}")

# Set up signal handlers for debugging
from celery.signals import task_received, task_prerun, task_success, task_failure, task_revoked, worker_ready

@task_received.connect
def task_received_handler(request, **kwargs):
    print(f"Task received: {request.id}, {request.task}")

@task_prerun.connect
def task_prerun_handler(task_id, task, **kwargs):
    print(f"Task about to run: {task_id}, {task.__name__}")

@task_success.connect
def task_success_handler(sender, result, **kwargs):
    print(f"Task succeeded: {sender.request.id}, result: {result}")

@task_failure.connect
def task_failure_handler(sender, task_id, exception, traceback, **kwargs):
    print(f"Task failed: {task_id}, exception: {exception}")

@task_revoked.connect
def task_revoked_handler(request, terminated, signum, expired, **kwargs):
    print(f"Task revoked: {request.id}, terminated: {terminated}")

@worker_ready.connect
def worker_ready_handler(**kwargs):
    print("Celery worker is ready!")
