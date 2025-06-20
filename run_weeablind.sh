#!/bin/bash
# This script attempts to activate a virtual environment and run weeablind.py

VENV_NAME="venv"
PYTHON_EXE="python3"

# Check if the virtual environment directory and activate script exist
if [ -f "${VENV_NAME}/bin/activate" ]; then
    echo "Activating virtual environment: ${VENV_NAME}"
    source "${VENV_NAME}/bin/activate"
else
    echo "Virtual environment '${VENV_NAME}' not found or activate script is missing."
    echo "Please ensure the virtual environment is created and named correctly,"
    echo "or modify the VENV_NAME variable in this script."
    echo "Trying to run with system Python 3..."
fi

echo "Starting Weeablind..."
"$PYTHON_EXE" weeablind.py

echo ""
echo "Weeablind has closed."
# Note: Deactivation of venv usually happens when the script ends or shell closes.
# If running this script with 'source ./run_weeablind.sh', then 'deactivate' would be needed.
# If running as './run_weeablind.sh', deactivation is generally automatic for that subshell.
