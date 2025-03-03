#!/bin/bash

# Current Date and Time (UTC): 2025-03-03 06:10:13
# Current User's Login: avhkbcj99

# Default values
DEFAULT_PORT=8080
DEFAULT_WORKERS=2
DEFAULT_LOG_LEVEL="info"

# Read port from command line or prompt for it
if [ -z "$1" ]; then
    read -p "Enter port number (default: ${DEFAULT_PORT}): " PORT
    PORT=${PORT:-$DEFAULT_PORT}
else
    PORT=$1
fi

# Setting environment variables for configuration
export BIND="0.0.0.0:${PORT}"
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-$DEFAULT_WORKERS}
export LOG_LEVEL=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}

# Script directory (to locate the gunicorn_conf.py)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_PATH="${SCRIPT_DIR}/deploy/gunicorn_conf.py"

# Application module - using main:app directly as specified
APP_MODULE="main:app"

# Screen session name
SCREEN_NAME="app_server_${PORT}"

# Display startup information
echo "===================================================="
echo "Starting application server"
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Bind: ${BIND}"
echo "Workers: ${GUNICORN_WORKERS}"
echo "Log level: ${LOG_LEVEL}"
echo "Config: ${CONFIG_PATH}"
echo "App module: ${APP_MODULE}"
echo "Screen session: ${SCREEN_NAME}"
echo "===================================================="

# Check if screen is installed
if ! command -v screen &> /dev/null; then
    echo "Error: screen is not installed. Please install it with 'sudo apt-get install screen' or equivalent."
    exit 1
fi

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Error: gunicorn is not installed. Please install it with 'pip install gunicorn'."
    exit 1
fi

# Check if the config file exists
if [ ! -f "${CONFIG_PATH}" ]; then
    echo "Error: Configuration file not found at ${CONFIG_PATH}"
    exit 1
fi

# Create logs directory if it doesn't exist
LOGS_DIR="${SCRIPT_DIR}/logs"
mkdir -p "${LOGS_DIR}"

# Create the start command
START_CMD="gunicorn -c ${CONFIG_PATH} ${APP_MODULE}"

# Start the application within a screen session
echo "Starting gunicorn in screen session '${SCREEN_NAME}'..."
screen -dmS ${SCREEN_NAME} bash -c "echo 'Starting application on port ${PORT}...' && ${START_CMD} && echo 'Application stopped at $(date)'"

# Check if screen session was created successfully
if screen -list | grep -q "${SCREEN_NAME}"; then
    echo "Application server started successfully in screen session '${SCREEN_NAME}'."
    echo "To attach to the session, run: screen -r ${SCREEN_NAME}"
    echo "To detach from the session, press Ctrl+A followed by D"
    echo "To kill the session, run: screen -X -S ${SCREEN_NAME} quit"

    # Save session info to a file
    SESSION_INFO_FILE="${LOGS_DIR}/session_${PORT}.info"
    {
        echo "Screen Session: ${SCREEN_NAME}"
        echo "Port: ${PORT}"
        echo "Started at: $(date)"
        echo "User: $(whoami)"
        echo "PID: $(screen -ls | grep ${SCREEN_NAME} | awk '{print $1}' | cut -d. -f1)"
    } > "${SESSION_INFO_FILE}"

    echo "Session information saved to: ${SESSION_INFO_FILE}"
else
    echo "Failed to start the application in screen session."
    exit 1
fi