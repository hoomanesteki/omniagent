# 🤖 OmniAgent: Multi-agent Data Analysis Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-195%20passing-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)]()

Imagine being able to talk to your data like a teammate. OmniAgent is an AI-powered, multi-agent assistant that lets you ask questions in plain English and instantly get meaningful insights, visualizations, and predictions. No coding, no wrestling with dashboards, just clear answers when you need them.

Most people spend too much time cleaning data, figuring out tools, and trying to extract insights manually. OmniAgent removes that friction by understanding your intent and automatically using the right specialized agents to do the work for you, turning complex data analysis into a simple, conversational experience.

---

## 📑 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Installation](#-installation)
- [Docker Deployment](#-docker-deployment)
- [Quick Start](#-quick-start)
- [Agents](#-agents)
- [Dynamic Agent](#-dynamic-agent-ai-powered)
- [Voice Assistant](#-voice-assistant)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Security](#-security)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗣️ **Natural Language** | Ask questions in plain English |
| 🎤 **Voice Input** | Speak your questions using browser microphone |
| 🤖 **7 Specialized Agents** | Stats, Viz, Aggregate, Predict, SQL, Dynamic, Voice |
| 🔮 **AI Code Generation** | Dynamic Agent creates custom analysis on-the-fly |
| 📊 **Interactive Charts** | Beautiful Plotly visualizations |
| 🧠 **Smart Routing** | Automatically finds the right agent for your query |
| 🔒 **Secure Execution** | Sandboxed code execution with 40+ security checks |
| 🎯 **ML Models** | Build predictive models with one command |
| 🐳 **Docker Ready** | One-command deployment with Docker |

---

## 🏗️ System Architecture

### High-Level Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                          (Streamlit Web App)                                 │
│                                                                              │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│    │  Text Input  │    │ Voice Input  │    │  Suggestions │                  │
│    │   (Chat)     │    │ (Microphone) │    │  (Buttons)   │                  │
│    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│           │                   │                   │                          │
│           └───────────────────┼───────────────────┘                          │
│                               ▼                                              │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │                      🧠 MASTER AGENT                                │   │
│    │                                                                     │   │
│    │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────────┐    │   │
│    │  │   Intent    │──▶│   Router    │──▶│  MCP Message Bus        │    │   │
│    │  │  Detection  │   │   Logic     │   │  (Agent Communication)  │    │   │
│    │  │ (200+ rules)│   │             │   │                         │    │   │
│    │  └─────────────┘   └─────────────┘   └───────────┬─────────────┘    │   │
│    │                                                   │                 │   │
│    │           Check: Is Dynamic Agent pending? ◄──────┤                 │   │
│    │                         │                         │                 │   │
│    │                    YES  │  NO                     │                 │   │
│    │                         ▼                         ▼                 │   │
│    │              ┌─────────────────┐      ┌─────────────────┐           │   │
│    │              │ Route to Dynamic│      │ Route by Intent │           │   │
│    │              │  (Confirmation) │      │ (stats/viz/etc) │           │   │
│    │              └─────────────────┘      └─────────────────┘           │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│    ┌───────────────────────────────┼─────────────────────────────────────┐   │
│    │                               ▼                                     │   │
│    │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │   │
│    │  │   📊   │ │   📈    │ │   📦   │ │   🤖   │ │   🔍    │ │   🔮   │  │   │
│    │  │ Stats  │ │  Viz   │ │  Agg   │ │ Predict│ │  SQL   │ │Dynamic │  │   │
│    │  │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │  │   │
│    │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │   │
│    │                                                                     │   │
│    │                          SPECIALIZED AGENTS                         │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│    ┌─────────────────────────────────────────────────────────────────────┐   │
│    │                        RESPONSE BUILDER                             │   │
│    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│    │   │   Content   │  │   Insights  │  │ Suggestions │  │  Figures  │  │   │
│    │   │  (Markdown) │  │   (Tips)    │  │  (Buttons)  │  │  (Plotly) │  │   │
│    │   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│    └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Message Communication Protocol (MCP)

Agents communicate using standardized MCP messages:

```python
MCPMessage(
    id: str,           # Unique message identifier
    type: MessageType, # QUERY, RESPONSE, ERROR, EVENT
    source: str,       # Sending agent name
    target: str,       # Receiving agent name
    content: str,      # Message content
    data: dict,        # Additional payload
    metadata: dict     # Timestamps, context
)
```

### Data Flow

```
User Query → Master Agent → Intent Detection → Route to Agent → Process → Response
     │                                              │
     │                                              ▼
     │                                    ┌─────────────────┐
     │                                    │ If Dynamic:     │
     │                                    │ 1. Offer        │
     │                                    │ 2. Plan (LLM)   │
     │                                    │ 3. Execute      │
     │                                    └─────────────────┘
     │                                              │
     └────────────────────────────────────────────◄─┘
```

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome/Edge recommended for voice features)

### Option 1: pip Install

```bash
# Clone the repository
git clone https://github.com/hoomanesteki/omniagent.git
cd omniagent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Option 2: Conda Install

```bash
# Clone the repository
git clone https://github.com/hoomanesteki/omniagent.git
cd omniagent

# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate omniagent

# Run the application
streamlit run app.py
```

### Option 3: Using Make

```bash
make install      # Install dependencies
make run          # Run the application
make test         # Run all tests
```

---

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build the image
docker build -t omniagent .

# Run the container
docker run -p 8501:8501 omniagent

# With API key for AI features
docker run -p 8501:8501 -e GROQ_API_KEY=your_key omniagent
```

### Using Docker Compose (Recommended)

```bash
# Create .env file with your API key (optional)
echo "GROQ_API_KEY=your_key_here" > .env

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Docker Commands Reference

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start in background |
| `docker-compose up -d --build` | Rebuild and start |
| `docker-compose down` | Stop and remove containers |
| `docker-compose logs -f` | Follow logs |
| `docker-compose restart` | Restart the service |

### Persistent Data

Mount a volume to persist uploaded data:

```bash
docker run -p 8501:8501 -v $(pwd)/data:/app/data omniagent
```

---

## 🚀 Quick Start

1. **Load Data**: Upload a CSV file or select a sample dataset from the sidebar
2. **Ask Questions**: Type naturally like "What's the average age?" or "Show histogram of price"
3. **Get Insights**: View visualizations, statistics, and AI-powered analysis

### Example Queries

| Query | Agent | Result |
|-------|-------|--------|
| "Show statistics" | 📊 Stats | Descriptive statistics |
| "Histogram of age" | 📈 Viz | Interactive histogram |
| "Count by gender" | 📦 Aggregate | Grouped counts |
| "Predict salary" | 🤖 Predict | ML model |
| "Show first 10 rows" | 🔍 SQL | Data preview |
| "Calculate rolling average" | 🔮 Dynamic | Custom analysis |
| "Calculate z-scores" | 🔮 Dynamic | Z-score normalization |

---

## 🤖 Agents

### Agent Overview

| Agent | Emoji | Purpose | Example Commands |
|-------|-------|---------|------------------|
| **Master** | 🧠 | Query routing & orchestration | (Internal) |
| **Stats** | 📊 | Statistical analysis | "mean of price", "check missing" |
| **Viz** | 📈 | Visualizations | "histogram", "scatter plot", "heatmap" |
| **Aggregate** | 📦 | GroupBy operations | "count by", "sum by", "average by" |
| **Predict** | 🤖 | Machine learning | "predict", "build model" |
| **SQL** | 🔍 | Data exploration | "show rows", "columns", "sample" |
| **Dynamic** | 🔮 | AI code generation | "rolling average", "find outliers", "z-scores" |
| **Voice** | 🎤 | Speech recognition | (Microphone input) |

---

## 🔮 Dynamic Agent (AI-Powered)

The Dynamic Agent handles requests beyond built-in capabilities by generating and executing custom Python code.

### Three-Step Confirmation Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DYNAMIC AGENT FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 1: OFFER (No LLM call - saves resources)                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ User: "Calculate rolling average of sales"                      │    │
│  │                                                                 │    │
│  │ Agent: "I can create a Rolling/Moving Average analysis.         │    │
│  │         This requires AI. Type 'yes' to proceed or 'no'."       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                     User types "yes"                                    │
│                              ▼                                          │
│  STEP 2: PLAN (LLM generates code)                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Agent: "Here's my plan:                                         │    │
│  │                                                                 │    │
│  │ ```python                                                       │    │
│  │ result = df['sales'].rolling(window=7).mean()                   │    │
│  │ ```                                                             │    │
│  │                                                                 │    │
│  │ Type 'yes' to execute or 'no' to cancel."                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                     User types "yes"                                    │
│                              ▼                                          │
│  STEP 3: EXECUTE (Sandboxed execution)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Agent: "✅ Analysis Complete!                                   │    │
│  │         [Shows results and visualization]"                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Supported Analysis Types

| Type | Keywords | Example |
|------|----------|---------|
| Rolling/Moving Average | "rolling", "moving average", "window" | "7-day rolling average" |
| Outlier Detection | "outlier", "anomaly", "IQR" | "Find outliers using IQR" |
| Z-Score/Standardization | "z-score", "normalize", "standardize" | "Calculate z-scores" |
| Regression Analysis | "regression", "trendline" | "Scatter with regression line" |
| Data Binning | "bin", "categorize", "bucket" | "Bin age into groups" |
| Ranking | "top", "bottom", "rank" | "Top 10 by sales" |
| Custom | Any other request | "Cumulative sum by date" |

### Enabling Dynamic Agent

1. Enable **AI Mode** in the sidebar
2. Enter your **Groq API Key** (free at [console.groq.com](https://console.groq.com))
3. Click **Validate & Save**
4. Ask any complex question!

---

## 🎤 Voice Assistant

OmniAgent supports **voice input** through your browser's built-in speech recognition.

> ⚠️ **Note**: Voice is **speech-to-text only** (you speak, agent responds with text).

### Requirements

| Requirement | Details |
|-------------|---------|
| **Browser** | Chrome, Edge, or Safari (Firefox limited) |
| **Microphone** | Built-in or external |
| **Permission** | Must allow browser microphone access |
| **HTTPS** | Required (localhost works for development) |

### How to Enable Voice

1. Toggle **Enable Voice** in the sidebar
2. Click **"🎤 Start Speaking"** button
3. **Allow microphone access** when browser prompts
4. Speak your question clearly
5. Query is automatically submitted

### Browser Microphone Setup

**Chrome:**
1. Click 🔒 lock icon in address bar
2. Find "Microphone" → Select "Allow"

**Edge:**
1. Click 🔒 lock icon in address bar
2. Click "Permissions for this site"
3. Set Microphone to "Allow"

**Safari:**
1. Safari → Preferences → Websites → Microphone
2. Allow for the OmniAgent site

### Troubleshooting Voice

| Issue | Solution |
|-------|----------|
| Microphone not working | Check browser permissions |
| No transcription | Speak clearly, reduce background noise |
| "Permission denied" | Reset site permissions and allow again |

---

## 📁 Project Structure

```
omniagent/
│
├── 📄 app.py                    # Main Streamlit entry point
├── 📄 requirements.txt          # Python dependencies
├── 📄 requirements-dev.txt      # Development dependencies
├── 📄 environment.yml           # Conda environment
├── 📄 Makefile                  # Build automation (40+ commands)
├── 📄 Dockerfile                # Docker image
├── 📄 docker-compose.yml        # Docker Compose config
├── 📄 pytest.ini                # Test configuration
├── 📄 README.md                 # This file
│
├── 📂 core/                     # Core utilities
│   ├── __init__.py
│   ├── config.py                # Configuration & settings
│   ├── analyzer.py              # DataAnalyzer class
│   └── llm.py                   # LLM client (Groq API)
│
├── 📂 agents/                   # Specialized agents
│   ├── __init__.py
│   ├── base.py                  # BaseAgent abstract class
│   ├── master_agent.py          # 🧠 Orchestrator
│   ├── stats_agent.py           # 📊 Statistics
│   ├── viz_agent.py             # 📈 Visualization
│   ├── aggregate_agent.py       # 📦 GroupBy
│   ├── predict_agent.py         # 🤖 ML prediction
│   ├── sql_agent.py             # 🔍 Data exploration
│   ├── dynamic_agent.py         # 🔮 AI code generation
│   └── voice_agent.py           # 🎤 Voice input
│
├── 📂 mcp/                      # Message Communication Protocol
│   ├── __init__.py
│   └── protocol.py              # MCPMessage, MCPBus
│
├── 📂 ui/                       # User interface
│   ├── __init__.py
│   ├── components.py            # Session, messages
│   ├── sidebar.py               # Sidebar UI
│   └── chat.py                  # Chat interface
│
├── 📂 tests/                    # Test suite (195 tests)
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
│
├── 📂 data/                     # Data files
│   ├── samples/                 # Sample datasets
│   └── uploads/                 # User uploads
│
└── 📂 docs/                     # Documentation
    ├── A_API_REFERENCE.md
    ├── B_MCP_PROTOCOL.md
    ├── C_TESTING.md
    ├── D_SECURITY.md
    └── E_DEPLOYMENT.md
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test suites
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-security      # Security tests

# Run with coverage
make coverage

# Run specific test file
pytest tests/unit/test_agents.py -v
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Core | 20+ | Config, DataAnalyzer, LLMClient |
| Agents | 50+ | All 7 agents, routing |
| MCP Protocol | 25+ | Messages, bus |
| Security | 40+ | Code safety, patterns |
| UI | 30+ | Help, about, messages |
| Integration | 20+ | End-to-end flows |

---

## 🔒 Security

### Dynamic Agent Security

The Dynamic Agent executes AI-generated code in a sandboxed environment with 40+ blocked patterns:

| Category | Blocked Patterns |
|----------|-----------------|
| **System Access** | `import os`, `import sys`, `subprocess` |
| **Code Injection** | `eval()`, `exec()`, `compile()` |
| **File Operations** | `open()`, `.read()`, `.write()` |
| **Network** | `requests.`, `urllib`, `socket` |
| **Reflection** | `globals()`, `locals()`, `getattr()` |
| **Dangerous Dunders** | `__builtins__`, `__class__` |

### Security Flow

```
Generated Code → Length Check → Pattern Check → Sandboxed Execution
                     ↓              ↓
                 Too long?      Dangerous?
                     ↓              ↓
                  REJECT         REJECT
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```env
# Groq API (for Dynamic Agent)
GROQ_API_KEY=your_api_key_here

# LLM Settings (optional)
LLM_MODEL=llama-3.3-70b-versatile
```

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `PAGE_TITLE` | "🤖 OmniAgent" | Browser tab title |
| `LLM_MODEL` | "llama-3.3-70b-versatile" | Groq model |
| `LLM_MAX_TOKENS` | 2000 | Max response tokens |
| `MAX_SUGGESTIONS` | 12 | Suggestion buttons |

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "No module named 'streamlit'" | Run `pip install -r requirements.txt` |
| Port 8501 in use | Use `streamlit run app.py --server.port=8502` |
| Voice not working | Use Chrome/Edge, allow microphone |
| Dynamic Agent fails | Check Groq API key is valid |
| Docker build fails | Ensure Docker daemon is running |

### Getting Help

- Check the [docs/](docs/) folder for detailed documentation
- Open an issue on GitHub
- Type "help" in OmniAgent chat

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Hooman Esteki**

- 🌐 Website: [esteki.ca](https://esteki.ca/)
- 📧 GitHub: [@hoomanesteki](https://github.com/hoomanesteki)

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) - Web framework
- [Plotly](https://plotly.com/) - Interactive charts
- [Groq](https://groq.com/) - Fast LLM inference
- [Scikit-learn](https://scikit-learn.org/) - Machine learning

---

<p align="center">
  Made with ❤️ by <a href="https://esteki.ca/">Hooman Esteki</a>
</p>
