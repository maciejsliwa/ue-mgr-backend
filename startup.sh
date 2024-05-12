#!/bin/sh
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b :8000 app:app --log-level warning