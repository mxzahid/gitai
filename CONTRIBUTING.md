# Contributing to Git-AI

Thank you for your interest in contributing to Git-AI! We welcome contributions from the community.

## Development Setup

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gitai.git
   cd gitai
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Install pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

4. Run tests:
   ```bash
   poetry run pytest
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure tests pass:
   ```bash
   poetry run pytest
   poetry run mypy gitai
   poetry run black gitai tests
   ```

3. Commit your changes:
   ```bash
   git commit -m "feat: add your feature description"
   ```

4. Push and create a pull request

## Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for type checking
- **flake8** for linting
- **pytest** for testing

All of these run automatically via pre-commit hooks.

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=gitai

# Run specific test file
poetry run pytest tests/test_commit.py
```

### Writing Tests

- Use descriptive test names
- Follow the existing test structure
- Include both unit and integration tests
- Mock external dependencies appropriately
- Test both success and failure scenarios

### Test Coverage

Aim for high test coverage

## Pull Request Process

1. **Title**: Use conventional commit format (e.g., `feat: add new feature`)
2. **Description**: Clearly describe what the PR does and why
3. **Tests**: Include tests for new functionality
4. **Documentation**: Update README/docs if needed
5. **Breaking Changes**: Clearly mark any breaking changes

## Issue Reporting

When reporting bugs or requesting features:

1. Use the issue templates
2. Provide clear reproduction steps
3. Include your environment (OS, Python version, etc.)
4. For bugs, include error messages and stack traces


## License

By contributing to GitAI, you agree that your contributions will be licensed under the MIT License.
