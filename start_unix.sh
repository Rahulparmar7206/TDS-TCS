#!/bin/bash

echo "================================================================================"
echo "TDS/TCS ANALYZER - Starting Application"
echo "================================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from https://www.python.org/"
    exit 1
fi

echo "Installing required packages..."
pip3 install -r requirements.txt

echo ""
echo "Starting TDS/TCS Analyzer..."
echo "Open your browser and go to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python3 tds_web_app.py
