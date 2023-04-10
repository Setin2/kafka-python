#!/bin/bash

# Set variables
IMAGE_NAME=$1
DOCKER_HUB_USERNAME=setin

# Build the image
docker build -t $IMAGE_NAME:latest $IMAGE_NAME

# Tag the image
docker tag $IMAGE_NAME:latest $DOCKER_HUB_USERNAME/$IMAGE_NAME:latest

# Push the image to Docker Hub
docker push $DOCKER_HUB_USERNAME/$IMAGE_NAME:latest
