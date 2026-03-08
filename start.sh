#!/bin/bash
set -e

echo "Starting OmniBot Easy Setup..."

# Setup Backend with uv
echo "Setting up Backend dependencies..."
cd backend
if [ ! -d ".venv" ]; then
    uv venv
fi
source .venv/bin/activate
uv pip install -r requirements.txt
python database.py
cd ..

# Setup Frontend with npm
echo "Setting up Frontend dependencies..."
cd frontend
npm install
cd ..

echo "====================================="
echo " OmniBot is ready!"
echo " Frontend: http://localhost:5173"
echo " Backend: http://localhost:8000"
echo " Press Ctrl+C to stop both servers."
echo "====================================="

# Run both servers in the background
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ../frontend
npm run dev -- --open &
FRONTEND_PID=$!

# Trap Ctrl+C to stop the servers
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" EXIT

wait
