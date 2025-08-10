#!/bin/bash

set -e

echo "🔍 Running Code Quality Checks..."
echo "================================"

echo ""
echo "📝 Running Black formatter..."
uv run black --check backend/

echo ""
echo "🔤 Running isort..."
uv run isort --check-only backend/

echo ""
echo "🐍 Running Flake8 linter..."
uv run flake8 backend/ --config /Users/vincent.cho/workspace/github.com/https-deeplearning-ai/starting-ragchatbot-codebase/.flake8

echo ""
echo "🔎 Running MyPy type checker..."
uv run mypy backend/

echo ""
echo "✅ All quality checks passed!"