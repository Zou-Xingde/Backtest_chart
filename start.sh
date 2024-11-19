#!/bin/bash
gunicorn 圖表程式:server --bind 0.0.0.0:$PORT
