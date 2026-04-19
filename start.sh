#!/bin/bash

PROJECT_PATH="/home/red/AgrivisionV1.0"
# DOUBLE CHECK THIS PATH - is the venv inside AgrivisionV1.0?
VENV_PATH="/home/red/venv"

onboard --hide &
ONBOARD_PID=$!

# Navigate to the directory so python finds local files easily
cd "$PROJECT_PATH"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Start server in background
python3 "$PROJECT_PATH/server.py" &
SERVER_PID=$!

# Start the main GUI app
python3 "$PROJECT_PATH/app.py"

# When app.py is closed, kill the server so the port is freed
kill $ONBOARD_PID
kill $SERVER_PID

rm -f /home/red/sed* echo "Agrivision closed and cleaned up."