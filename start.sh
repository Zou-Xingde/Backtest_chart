#!/bin/bash
gunicorn chart_app:server --bind 0.0.0.0:$PORT
