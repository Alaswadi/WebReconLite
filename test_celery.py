#!/usr/bin/env python
# Test script to check if Celery is working

from celery_app import celery

@celery.task
def add(x, y):
    print(f"Adding {x} + {y}")
    return x + y

if __name__ == "__main__":
    print("Sending task to Celery...")
    result = add.delay(4, 4)
    print(f"Task ID: {result.id}")
    print("Task sent. Check Celery worker logs to see if it's processed.")
