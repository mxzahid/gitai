# Git-AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Generate Conventional Commit messages and changelog sections using AI. Simple to install, works with
Use Local models with Ollama or OpenAI, gracefully degrades when no AI is available.

## Features

- **AI-Powered**: Generate commit messages using OpenAI or local Ollama models
- **Conventional Commits**: Follows strict Conventional Commit formatting rules
- **Changelog Generation**: Create Keep a Changelog formatted sections
- **Git Hook Integration**: Automatic commit message generation on `git commit`
- **Fallback Mode**: Works without AI using intelligent heuristics
- **Cross-Platform**: Linux, macOS support
- **Zero Dependencies**: Single Python package, minimal runtime deps

## Quick Start (60 seconds)

### Install

```bash
# using pipx (recommended)
pipx install enhanced-git

# or using pip
pip install enhanced-git
```

### Setup (Optional AI Integration)

**With OpenAI:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**With Ollama (Local AI):**
```bash
# install Ollama and pull a model
ollama pull qwen2.5-coder:3b

# set environment variables
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="qwen2.5-coder:3b"
```

### Basic Usage

```bash
# stage some changes
git add .

# Install Git hook for automatic generation
git-ai hook install

#if using git-ai hook, then just do git commit -m "some sample message"
#if not using git-ai hook use this:
git commit -m "$(git-ai commit)"


# generate changelog
git-ai changelog --since v1.0.0 --version v1.1.0
```

## Usage

### Commands

#### `git-ai commit`

Generate a commit message from staged changes.

```bash
# Basic usage
git-ai commit

# Preview without committing
git-ai commit --dry-run

# Subject line only
git-ai commit --no-body

# Force plain style (no conventional format)
git-ai commit --style plain

# Used by Git hook
git-ai commit --hook /path/to/.git/COMMIT_EDITMSG
```

#### `git-ai hook install`

Install Git hook for automatic commit message generation.

```bash
# Install hook
git-ai hook install

# Force overwrite existing hook
git-ai hook install --force

# Remove hook
git-ai hook uninstall
```

#### `git-ai changelog`

Generate changelog section from commit history.

```bash
# generate changelog from commits since v1.0.0
git-ai changelog --since v1.0.0

# with version header
git-ai changelog --since v1.0.0 --version v1.1.0

# custom output file
git-ai changelog --since v1.0.0 --output HISTORY.md

# different end reference
git-ai changelog --since v1.0.0 --to main
```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model name (default: qwen2.5-coder:3b)

### Configuration File

GitAI supports optional configuration via a `.gitai.toml` file in your git repository root. This allows you to customize behavior beyond environment variables.

**Auto-detection**: GitAI automatically detects your LLM provider based on environment variables (no config file needed!):
- If `OPENAI_API_KEY` is set → uses OpenAI
- If `OLLAMA_BASE_URL` or `OLLAMA_MODEL` is set → uses Ollama
- Otherwise → falls back to OpenAI

**Custom configuration**: Create `.gitai.toml` in your project root for advanced settings:

```toml
[llm]
provider = "ollama"          # "openai" | "ollama"
model = "qwen2.5-coder:3b"        # I suggest using one of: qwen2.5-coder:3b, qwen2.5-coder:1.5b, codellama:7b, deepseek-coder:6.7b
max_tokens = 300
temperature = 0.1
timeout_seconds = 45

[commit]
style = "conventional"       # "conventional" | "plain"
scope_detection = true
include_body = true
include_footers = true
wrap_width = 72

[changelog]
grouping = "type"            # group by Conventional Commit type
heading_style = "keep-a-changelog"

[debug]
debug_mode = false
```

## How It Works

### Commit Message Generation

1. **Diff Analysis**: Parses `git diff --staged` to understand changes
2. **Type Inference**: Detects commit type from file paths and content:
   - `tests/` → `test`
   - `docs/` → `docs`
   - `fix`/`bug` in content → `fix`
   - New files → `feat`
3. **AI Enhancement**: Uses LLM to polish the message while preserving accuracy
4. **Formatting**: Ensures Conventional Commit compliance:
   - Subject < 70 chars
   - `type(scope): description` format
   - Proper body wrapping at 72 columns

### Changelog Generation

1. **Commit Parsing**: Extracts commits between references
2. **Grouping**: Groups by Conventional Commit types
3. **AI Polish**: Improves clarity while preserving facts
4. **Insertion**: Adds new section to top of CHANGELOG.md

### Fallback Mode

When no AI is configured, GitAI uses intelligent heuristics:

- Path-based type detection
- Content analysis for keywords
- Statistical analysis of changes
- Scope inference from directory structure

## Development

### Setup

```bash
# clone repository
git clone https://github.com/yourusername/git-ai.git
cd gitai

# install with dev dependencies
pip install -e ".[dev]"

# run tests
pytest

# run linting
ruff check .
mypy gitai
```

### Project Structure

```
gitai/
├── cli.py              # Main CLI entry point
├── commit.py           # Commit message generation
├── changelog.py        # Changelog generation
├── config.py           # Configuration management
├── constants.py        # Prompts and constants
├── diff.py             # Git diff parsing and chunking
├── hook.py             # Git hook management
├── providers/          # LLM providers
│   ├── base.py
│   ├── openai_provider.py
│   └── ollama_provider.py
├── util.py             # Utility functions
└── __init__.py

tests/                  # Test suite
├── test_commit.py
├── test_changelog.py
├── test_diff.py
└── test_hook_integration.py
```

## Contributing

I welcome contributions! Be kind

### Development Requirements

- Python 3.11+
- Poetry for dependency management
- Pre-commit for code quality

### Testing

```bash
# run test suite
pytest

# with coverage
pytest --cov=gitai --cov-report=html

# run specific tests
pytest tests/test_commit.py -v
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Privacy & Security

- **No Code Storage**: Your code never leaves your machine
- **Local AI Option**: Use Ollama for complete local processing
- **API Usage**: Only sends commit diffs and prompts to configured LLM
- **Graceful Degradation**: Works without any network access

## Troubleshooting

### No staged changes
```
Error: No staged changes found. Did you forget to run 'git add'?
```
**Solution**: Stage your changes with `git add` before running `git-ai commit`

### Missing API key
```
Warning: OPENAI_API_KEY environment variable is required
```
**Solution**: Set your API key or use Ollama for local AI

### Hook conflicts
```
Warning: Existing commit-msg hook found
```
**Solution**: Use `git-ai hook install --force` to overwrite, or manually merge

### Network timeouts
```
Error: Ollama API error: Connection timeout
```
**Solution**: Check Ollama is running: `ollama serve`

### Large diffs
GitAI automatically chunks large diffs to stay within LLM token limits

## Examples

### Example Commit Messages

**AI-Generated:**
```
feat(auth): add user registration and login system

- Implement user registration with email validation
- Add login endpoint with JWT token generation
- Create password hashing utilities
- Add input validation and error handling
```

**Fallback Mode:**
```
feat(src): add user authentication module

- add src/auth.py (45 additions)
- update src/models.py (12 additions, 3 deletions)
```

### Example Changelog

```markdown
## [v1.1.0] - 2024-01-15

### Features
- **auth**: Add user registration and login system (#123)
- **api**: Implement RESTful user management endpoints

### Fixes
- **core**: Fix null pointer exception in user validation (#456)
- **db**: Resolve connection timeout issues

### Documentation
- Update API documentation with authentication examples
- Add installation instructions for local development
```
