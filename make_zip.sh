#!/usr/bin/env bash
zip -r wm-service-chatbot.zip . -x "*.pyc" "__pycache__/*" "wm_manual.faiss" "wm_manual_meta.json" "logs/*"
echo "Created wm-service-chatbot.zip"
