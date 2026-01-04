# Contributing to OmniAgent

Thanks for your interest in contributing! OmniAgent is a multi-agent data
analysis assistant built with Streamlit and Python. This guide covers how to
set up the project, make changes, and submit contributions.

## Ways to Contribute

- Report bugs and request features via GitHub Issues
- Improve documentation or examples
- Add new agents, analysis capabilities, or tests
- Fix bugs or improve performance

## Development Setup

### Prerequisites

- Python 3.8+
- pip or conda
- Optional: Docker

### Local Setup (pip)

```bash
git clone https://github.com/hoomanesteki/omniagent.git
cd omniagent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Local Setup (conda)

```bash
git clone https://github.com/hoomanesteki/omniagent.git
cd omniagent
conda env create -f environment.yml
conda activate omniagent
```

### Running the App

```bash
streamlit run app.py
```

### Running Tests

```bash
make test
```

## Project Structure

- `agents/`: Specialized agent implementations
- `core/`: Core utilities and configuration
- `mcp/`: Message Communication Protocol
- `ui/`: Streamlit UI components
- `tests/`: Test suite

## Development Guidelines

- Keep changes focused and scoped to a single purpose.
- Add or update tests for any behavior changes.
- Favor small, well-documented changes over sweeping refactors.
- Avoid adding insecure code paths, especially in dynamic execution areas.

## Commit Messages

Use clear, concise commit messages describing the change. Example:

```
feat: add anomaly detection to dynamic agent
```

## Submitting a Pull Request

1. Create a branch for your change.
2. Ensure tests pass.
3. Open a PR with a clear title and description.
4. Link any relevant issues.

## Community

Please read and follow the [Code of Conduct](CODE_OF_CONDUCT.md).
