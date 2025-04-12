#!/usr/bin/env python
# Test script to check if Redis is working

import redis
import os
import time

def test_redis():
    # Get Redis connection details
    broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    print(f"Connecting to Redis at {broker_url}...")
    
    # Parse the Redis URL
    if broker_url.startswith('redis://'):
        host_port = broker_url[8:].split('/')[0]
        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 6379
    else:
        host = 'localhost'
        port = 6379
    
    print(f"Parsed Redis host: {host}, port: {port}")
    
    # Connect to Redis
    try:
        r = redis.Redis(host=host, port=port, db=0)
        print("Connected to Redis.")
        
        # Test Redis connection
        print("Testing Redis connection...")
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        print(f"Retrieved value: {value}")
        
        # Test Redis pub/sub
        print("Testing Redis pub/sub...")
        pubsub = r.pubsub()
        pubsub.subscribe('test_channel')
        
        # Publish a message
        r.publish('test_channel', 'test_message')
        
        # Wait for the message
        print("Waiting for message...")
        for message in pubsub.listen():
            print(f"Received message: {message}")
            if message['type'] == 'message':
                break
        
        print("Redis is working correctly!")
        return True
    except Exception as e:
        print(f"Error connecting to Redis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_redis()
