#!/usr/bin/env python
# Test script to check if Celery is processing tasks

import os
import time
from celery_app import celery

@celery.task(name='test_task')
def test_task(x, y):
    """A simple test task that adds two numbers."""
    print(f"Test task started: Adding {x} + {y}")
    # Simulate a long-running task
    for i in range(5):
        print(f"Test task progress: {i+1}/5")
        time.sleep(1)
    result = x + y
    print(f"Test task completed: {x} + {y} = {result}")
    return result

if __name__ == "__main__":
    print("Sending test task to Celery...")
    
    # Get broker URL from environment
    broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    print(f"Broker URL: {broker_url}")
    
    # Send the task
    result = test_task.delay(4, 4)
    print(f"Task ID: {result.id}")
    
    # Wait for the task to complete
    print("Waiting for task to complete...")
    for i in range(10):
        if result.ready():
            print(f"Task completed: {result.get()}")
            break
        print(f"Task still running... ({i+1}/10)")
        time.sleep(1)
    else:
        print("Task did not complete within 10 seconds.")
