#!/bin/bash
# Setup script for ML recommendation engine

echo "========================================="
echo "Fora ML Recommendation Engine Setup"
echo "========================================="
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd server
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo "✅ Python dependencies installed"
echo ""

# Generate sample data (optional)
echo "🎲 Would you like to generate sample training data? (y/n)"
read -r generate_sample

if [ "$generate_sample" = "y" ] || [ "$generate_sample" = "Y" ]; then
    echo "Generating sample data..."
    python train_with_sample_data.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Sample data generated successfully"
    else
        echo "⚠️  Sample data generation failed (you can run this later)"
    fi
fi

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "The ML recommendation engine will:"
echo "  • Run automatically in the background when the server starts"
echo "  • Update recommendations every hour"
echo "  • Train on user interactions daily at 2 AM"
echo ""
echo "To start the server:"
echo "  cd server"
echo "  python run.py"
echo ""
echo "The home page will display personalized recommendations!"
echo "========================================="
