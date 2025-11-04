#!/bin/bash

# --- Configuration ---
PROJECT_PATH="/home/red/AgrivisionV1.0"
VENV_PATH="/home/red/venv"
SERVER_PID=0

# --- Cleanup Function ---
# This function will be called when the script exits
cleanup() {
  echo " " # Newline for cleaner output
  echo "Shutting down..."

  # Check if the server process is running (PID is not 0)
  if [ $SERVER_PID -ne 0 ]; then
    echo "Stopping background server (PID: $SERVER_PID)..."
    # Kill the specific server process
    # Using 'kill' with the PID is safer than 'pkill'
    kill $SERVER_PID
  fi

  # Deactivate the virtual environment
  echo "Deactivating venv. Exiting."
  # Check if deactivate function exists before calling
  if declare -f deactivate > /dev/null; then
    deactivate
  fi
}

# --- Trap ---
# This "traps" the script's exit signals (normal exit, Ctrl+C, etc.)
# and runs the 'cleanup' function whenever it's triggered.
# EXIT: Normal script finish (when app.py closes)
# INT: Interrupt (e.g., Ctrl+C)
# TERM: Terminate signal
trap cleanup EXIT INT TERM

# --- Main Execution ---

# 1. Activate the virtual environment
echo "Activating venv..."
source "$VENV_PATH/bin/activate"

# 2. Start the server.py script in the background
echo "Starting background server..."
# Run the server and silence its stdout/stderr if you don't want to see it
# nohup python3 "$PROJECT_PATH/server.py" > /dev/null 2>&1 &
# Or let it print to the console:
python3 "$PROJECT_PATH/server.py" &

# 3. Capture the PID of the last backgrounded process
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# 4. Start the main desktop application (app.py) in the foreground
# The script will pause here until app.py is closed.
echo "Launching main application (press Ctrl+C or close app to exit)..."
python3 "$PROJECT_PATH/app.py"

# 5. When app.py closes, the script will end,
#    which triggers the 'EXIT' trap and runs the 'cleanup' function.
