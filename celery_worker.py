#!/usr/bin/env python
# This file is used as an entry point for Celery workers

import os
import sys

# Print Python version and environment for debugging
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Environment variables: {os.environ}")

# Import Celery instance
print("Importing Celery instance...")
from celery_app import celery

# Import Flask app
print("Importing Flask app...")
from app import create_app

# Create Flask app context for Celery tasks
print("Creating Flask app...")
app = create_app()
print("Pushing app context...")
app.app_context().push()
print("App context pushed.")

# Set up Celery to work with Flask app context
print("Setting up Celery to work with Flask app context...")
TaskBase = celery.Task

class ContextTask(TaskBase):
    abstract = True

    def __call__(self, *args, **kwargs):
        print(f"Task called: {self.name}, args: {args}, kwargs: {kwargs}")
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)

celery.Task = ContextTask
print("Celery Task class updated.")

print("Celery worker initialization complete.")
