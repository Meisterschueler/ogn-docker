# ogn-docker

## Features
- [x] OGN configuration with environment variables instead of libconfig files
- [x] ogn-rf and ogn-decode do not start if configuration is invalid or incomplete
- [x] aprs-proxy for the outgoing and incoming aprs traffic, filter scripts are written in Python
- [x] multiarch (linux/arm/v7, linux/arm64, linux/amd64) images available for all docker containers: [dockerhub](https://hub.docker.com/u/kammermark)

## Installation
### Configuration
Copy `.env.example` and rename it to `.env` then set the values accordingly.

## Docker images
Just run the makefile to create the docker images.

`$ make`

## Start the receiver

`$ docker compose up -d`
