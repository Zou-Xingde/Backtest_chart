#!/bin/bash
gunicorn 圖表程式:app.server --bind 0.0.0.0:$PORT
