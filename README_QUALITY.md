# Code Quality Setup

This project now includes essential code quality tools for maintaining consistent and high-quality Python code.

## Quick Start

```bash
# Install all dependencies including dev tools
uv sync
uv sync --group dev

# Auto-format all code
./scripts/format.sh

# Run all quality checks
./scripts/quality.sh

# Setup pre-commit hooks (recommended)
./scripts/pre-commit.sh
```

## Tools Included

### Black (Code Formatter)
- Automatically formats Python code to a consistent style
- Line length: 88 characters
- Compatible with Python 3.11+

### isort (Import Sorter)
- Automatically sorts and organizes imports
- Configured to work with Black's formatting

### Flake8 (Linter)
- Checks for Python style guide violations
- Max line length: 120 characters
- Configured with sensible exclusions

### MyPy (Type Checker)
- Static type checking for Python
- Helps catch type-related bugs early
- Currently shows some type hints that can be improved

### Pre-commit Hooks
- Automatically runs formatters before each commit
- Prevents committing poorly formatted code
- Includes additional checks for:
  - Trailing whitespace
  - End of file fixing
  - YAML/JSON/TOML validation
  - Large file detection
  - Merge conflict detection

## Configuration Files

- `pyproject.toml` - Tool configurations for Black, isort, and MyPy
- `.flake8` - Flake8 linter configuration
- `.pre-commit-config.yaml` - Pre-commit hook configuration

## Scripts

All scripts are located in the `scripts/` directory:

- `format.sh` - Auto-formats all code with Black and isort
- `quality.sh` - Runs all quality checks (format check, lint, type check)
- `pre-commit.sh` - Sets up pre-commit hooks for the repository

## Usage in Development

1. **Before committing**: Run `./scripts/format.sh` to auto-format your code
2. **To check quality**: Run `./scripts/quality.sh` to ensure code meets standards
3. **For automatic checking**: Run `./scripts/pre-commit.sh` once to setup hooks

## Current Status

✅ All Python files have been formatted with Black and isort
✅ Most linting issues resolved (some long lines in docstrings remain)
⚠️ MyPy shows some type annotation improvements that can be made

## Next Steps

To improve code quality further:
1. Add missing type annotations where MyPy indicates
2. Consider adding more comprehensive type hints
3. Set up CI/CD pipeline to run quality checks automatically