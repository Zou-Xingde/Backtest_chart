#!/bin/bash
gunicorn 回測圖表.圖表程式:app --bind 0.0.0.0:$PORT
