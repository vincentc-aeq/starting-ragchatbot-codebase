#!/bin/bash

set -e

echo "🎨 Auto-formatting code..."
echo "=========================="

echo ""
echo "📝 Running Black formatter..."
uv run black backend/

echo ""
echo "🔤 Running isort..."
uv run isort backend/

echo ""
echo "✨ Code formatting complete!"