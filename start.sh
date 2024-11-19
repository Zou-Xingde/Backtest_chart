#!/bin/bash
gunicorn 圖表程式:app --bind 0.0.0.0:$PORT
