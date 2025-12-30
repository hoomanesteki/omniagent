# OmniAgent 📊

**AI-Powered Data Analyst** - Chat with your data using natural language.

## Features

- 💬 **Natural Language Interface** - Ask questions in plain English
- 📊 **6 Specialized Agents** - Schema, SQL, EDA, Statistics, Regression, Plot
- 📈 **Visualizations** - Histograms, scatter plots, bar charts, heatmaps
- 🔍 **Data Profiling** - Missing values, outliers, correlations
- 🤖 **Powered by Groq** - Fast, free LLM inference

## Quick Start

### 1. Setup

```bash
conda env create -f environment.yml
conda activate omniagent
```

### 2. Get API Key

Go to [console.groq.com/keys](https://console.groq.com/keys) and create a free key.

### 3. Configure

```bash
cp .env.example .env
# Edit .env and add: GROQ_API_KEY=your-key
```

### 4. Run

```bash
python tests/test_api.py    # Test API
python tests/test_all.py    # Full tests
streamlit run app.py        # Launch app
```

## Project Structure

```
omniagent/
├── app.py                  # Streamlit UI
├── omniagent/
│   ├── agents/             # 6 specialized agents
│   ├── master/             # Orchestrator agent
│   ├── mcp/                # MCP protocol
│   ├── data/               # DuckDB layer
│   └── models/             # Pydantic models
├── tests/                  # Test suite
├── data/samples/           # Sample CSVs
└── .env.example            # Config template
```

## Agents

| Agent | Purpose |
|-------|---------|
| SchemaAgent | Dataset structure, columns, samples |
| SQLAgent | Safe SQL queries |
| EDAAgent | Profiling, missing values, outliers |
| StatsAgent | Statistics, correlations, groupby |
| RegressionAgent | Linear regression modeling |
| PlotAgent | Visualizations |

## Sample Queries

- "Summarize this dataset"
- "Are there any missing values?"
- "Show statistics for the price column"
- "Create a histogram of ages"
- "What columns are correlated?"

## License

MIT
