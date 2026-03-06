#!/bin/bash

# Test script for the backend API

echo "Testing backend API..."

# Test health endpoint
echo -e "\n1. Testing health endpoint:"
curl -X GET http://localhost:8000/health

# Test predict endpoint with a sample image
echo -e "\n\n2. Testing predict endpoint:"
echo "Please ensure you have a test image and run:"
echo "curl -X POST -F 'image=@/path/to/your/test-image.jpg' http://localhost:8000/predict"

echo -e "\n\nDone!"
