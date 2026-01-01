# 🤖 OmniAgent: AI-Powered Data Analysis Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**OmniAgent** is an intelligent, multi-agent data analysis assistant that helps you explore, visualize, and understand your data through natural conversation.



---

## 🌟 Features

- **Natural Language Interface** - Ask questions in plain English
- **Voice Assistant** - Two-way voice conversation (speak & listen)
- **Multi-Agent Architecture** - 6 specialized agents working together
- **Smart Routing** - Automatically finds the right agent for your query
- **Interactive Visualizations** - Beautiful Plotly charts with zoom/pan
- **Machine Learning** - Build predictive models with one command
- **Data Aggregation** - GroupBy, pivot, and summary operations
- **AI Enhancement** - Optional Groq LLM for smarter responses

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER QUERY                               │
│                             ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   🧠 MASTER AGENT                          │  │
│  │         Natural Language Understanding & Routing           │  │
│  │                Message Communication Protocol              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                             ↓                                    │
│      ┌────────┬─────────┬─────────┬──────────┬─────────┐         │
│      ↓        ↓         ↓         ↓         ↓          ↓         │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │
│  │  📊  │  │  📈   │  │  📦  │  │  🤖  │   │  🔍  │  │  🧠  │      │
│  │Stats │  │ Viz  │  │ Agg  │  │Pred  │  │ SQL  │  │Master│      │
│  │Agent │  │Agent │  │Agent │  │Agent │  │Agent │  │Agent │      │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘      │
│                             ↓                                    │
│                       RESPONSE + INSIGHTS                        │
└──────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Emoji | Responsibilities |
|-------|-------|------------------|
| **Master** | 🧠 | Query understanding, routing, orchestration |
| **Stats** | 📊 | Statistics, summaries, missing values, distributions |
| **Viz** | 📈 | Charts, plots, heatmaps, visualizations |
| **Aggregate** | 📦 | GroupBy, pivot tables, aggregations |
| **Predict** | 🤖 | Machine learning models, predictions |
| **SQL** | 🔍 | Data preview, schema, sampling |

---

## 🎤 Voice Assistant

OmniAgent includes a **two-way voice conversation** feature:

| Feature | Description |
|---------|-------------|
| **🎤 Speak** | Click "Start Speaking" and ask your question by voice |
| **🔊 Listen** | Agent speaks responses back to you automatically |
| **⚙️ Settings** | Adjust voice speed and pitch |

### How to Use Voice:
1. Enable **Voice** toggle in the sidebar
2. Click **"Start Speaking"** button
3. Ask your question (e.g., "Show me statistics")
4. Your question auto-submits to chat
5. Agent responds in text AND speaks the answer!

*Works best in Chrome or Edge browsers*

---

## 📁 Project Structure

```
omniagent/
├── app.py                    # Main entry point
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── .env.example              # Environment template
│
├── core/                     # Core utilities
│   ├── __init__.py
│   ├── config.py             # Configuration & CSS styles
│   ├── analyzer.py           # DataAnalyzer class
│   └── llm.py                # LLM client (Groq API)
│
├── agents/                   # Specialized agents
│   ├── __init__.py
│   ├── base.py               # BaseAgent abstract class
│   ├── master_agent.py       # Orchestrator with MCP
│   ├── stats_agent.py        # Statistical analysis
│   ├── viz_agent.py          # Visualizations
│   ├── aggregate_agent.py    # GroupBy & aggregations
│   ├── predict_agent.py      # Machine learning
│   └── sql_agent.py          # Data queries
│
├── mcp/                      # Message Communication Protocol
│   ├── __init__.py
│   └── protocol.py           # MCPMessage, MCPBus, AgentResponse
│
├── ui/                       # User interface
│   ├── __init__.py
│   ├── components.py         # Session, loading, messages
│   ├── sidebar.py            # Sidebar UI
│   └── chat.py               # Chat & suggestions
│
└── data/
    ├── samples/              # Sample datasets
    │   ├── fitness_tracker.csv
    │   ├── nyc_airbnb.csv
    │   └── ecommerce_sales.csv
    └── uploads/              # User uploads
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/yourusername/omniagent.git
cd omniagent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure (Optional - for AI features)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Groq API key
# Get free key at: https://console.groq.com
GROQ_API_KEY=gsk_your_key_here
```

### 3. Run

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 💬 Usage Examples

### Statistics
```
"What's the average age?"
"Show me statistics"
"Check for missing values"
"What's the median price?"
```

### Visualization
```
"Histogram of age"
"Scatter plot price vs quantity"
"Correlation heatmap"
"Bar chart of categories"
```

### Aggregation
```
"Count by gender"
"Sum sales by region"
"Average price by category"
"Group by status"
```

### Machine Learning
```
"Predict sales"
"Build a model"
"What can I predict?"
"Feature importance"
```

### Data Exploration
```
"Show first 10 rows"
"What columns do I have?"
"Random sample"
"Data structure"
```

---

## 🔧 Technology Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit |
| **Visualization** | Plotly |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn |
| **AI/NLU** | Groq (LLaMA 3.3 70B) |
| **Architecture** | MCP (Message Communication Protocol) |

---

## 📡 Message Communication Protocol (MCP)

OmniAgent uses a custom MCP for agent communication:

```python
# Message structure
MCPMessage(
    id="unique-id",
    type=MessageType.QUERY,
    source="master",
    target="stats",
    content="show statistics",
    data={},
    metadata={}
)

# Agent response
AgentResponse(
    content="## Statistics...",
    figure=plotly_fig,
    dataframe=df,
    insights="Key findings...",
    suggestions=["Next action 1", "Next action 2"]
)
```

### Message Flow

1. **User** sends natural language query
2. **Master Agent** detects intent via pattern matching
3. **MCP Bus** routes message to appropriate agent
4. **Specialized Agent** processes and returns response
5. **UI** renders response with charts, tables, insights

---

## 🎯 Agent Details

### 📊 Stats Agent
- Descriptive statistics (mean, median, std, etc.)
- Missing value analysis
- Distribution analysis
- Data quality checks

### 📈 Viz Agent
- Histograms
- Scatter plots
- Bar charts (horizontal for better readability)
- Box plots (outlier detection)
- Correlation heatmaps
- Pie charts
- Multi-panel visualizations

### 📦 Aggregate Agent
- Count by category
- Sum/Average/Max/Min by group
- Group summaries
- Pivot-style operations

### 🤖 Predict Agent
- Classification models
- Regression models
- Feature importance analysis
- Model evaluation metrics
- Interactive model builder

### 🔍 SQL Agent
- Data preview (head/tail/sample)
- Schema exploration
- Column information

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for AI features | No |
| `LLM_MODEL` | Model name (default: llama-3.3-70b-versatile) | No |

---

## 📋 Requirements

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.15.0
scikit-learn>=1.3.0
python-dotenv>=1.0.0
requests>=2.31.0
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Hooman Esteki**
- Website: [esteki.ca](https://esteki.ca/)
- GitHub: [@hoomanesteki](https://github.com/hoomanesteki)

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io) for the amazing web framework
- [Plotly](https://plotly.com) for interactive visualizations
- [Groq](https://groq.com) for blazing fast AI inference
- [Scikit-learn](https://scikit-learn.org) for machine learning

---

Made with ❤️ by [Hooman Esteki](https://esteki.ca/)
