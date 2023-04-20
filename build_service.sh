#!/bin/bash

# Set variables
IMAGE_NAME=$1
DOCKER_HUB_USERNAME=setin

# Build the image
# Images will be built from the parent directory, as we also need to copy files from the shared-files directory
docker build -t $IMAGE_NAME:latest -f $IMAGE_NAME/Dockerfile .

# Tag the image
docker tag $IMAGE_NAME:latest $DOCKER_HUB_USERNAME/$IMAGE_NAME:latest

# Push the image to Docker Hub
docker push $DOCKER_HUB_USERNAME/$IMAGE_NAME:latest
