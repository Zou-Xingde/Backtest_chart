#!/bin/bash
# gunicorn chart_app:server --bind 0.0.0.0:$PORT
gunicorn EX-01:server --bind 0.0.0.0:$PORT