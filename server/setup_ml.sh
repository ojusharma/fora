#!/bin/bash
# ML Model Setup Script
# Run this after cloning the repository or on deployment

set -e

echo "============================================"
echo "ML Model Setup for Fora"
echo "============================================"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed"
    exit 1
fi

# Check if we're in the server directory
if [ ! -f "train_with_sample_data.py" ]; then
    echo "Changing to server directory..."
    cd server || exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Train the model
echo ""
echo "🤖 Training ML model with sample data..."
echo ""
python train_with_sample_data.py

echo ""
echo "============================================"
echo "✅ ML Model Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Start the server: uvicorn app.main:app --reload"
echo "2. Check model_info.txt for training details"
echo "3. Set up cron jobs for periodic retraining"
echo ""
