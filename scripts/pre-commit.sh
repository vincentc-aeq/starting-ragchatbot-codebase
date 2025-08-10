#!/bin/bash

set -e

echo "🔧 Setting up pre-commit hooks..."
echo "================================="

echo ""
echo "📦 Installing pre-commit hooks..."
uv run pre-commit install

echo ""
echo "🔍 Running pre-commit on all files..."
uv run pre-commit run --all-files || true

echo ""
echo "✅ Pre-commit setup complete!"
echo ""
echo "Pre-commit will now run automatically before each git commit."
echo "To run manually: uv run pre-commit run --all-files"