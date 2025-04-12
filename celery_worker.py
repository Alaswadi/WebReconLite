#!/usr/bin/env python
# This file is used as an entry point for Celery workers

from celery_app import celery
from app import create_app

# Create Flask app context for Celery tasks
app = create_app()
app.app_context().push()

# Set up Celery to work with Flask app context
TaskBase = celery.Task

class ContextTask(TaskBase):
    abstract = True

    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)

celery.Task = ContextTask
