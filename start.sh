#!/bin/sh

export MONGODB_URL="mongodb://localhost:27017/setpoints?retryWrites=true&w=majority"

uvicorn app:app --reload \
        --header "server:ece531endpoint/0.0.1" \
        --host 0.0.0.0 --port 8989 \
        --log-config=log_config.yaml \
        --workers 5 \
        --limit-concurrency 10

