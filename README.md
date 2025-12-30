# OmniAgent

OmniAgent is an agentic AI system for interactive analysis of arbitrary CSV datasets.
It acts like a ChatGPT-style data analyst: you upload a dataset, then ask natural-language
questions to explore, analyze, visualize, and model the data.

The system is built around a Master Agent that orchestrates specialized agents
(SQL, EDA, Regression, Plotting) via MCP (Model Context Protocol).

----------------------------------------------------------------
## WHAT OMNIAGENT DOES
----------------------------------------------------------------

- Accepts any CSV dataset (numeric, categorical, mixed)
- Infers schema, types, and basic statistics automatically
- Supports natural-language questions about the data
- Runs safe, read-only SQL queries
- Performs aggregations and exploratory data analysis
- Fits regression models and explains results
- Generates plots and visual summaries
- Explains all outputs in plain English

----------------------------------------------------------------
## VISION
----------------------------------------------------------------

Build a best-in-class, general-purpose AI data analyst that:
- Feels like ChatGPT for tabular data
- Uses explicit, auditable tool calls (no hidden code execution)
- Scales from a local MVP to a production system
- Serves as a reference architecture for modern agentic systems

----------------------------------------------------------------
## SYSTEM FLOW (HIGH LEVEL)
----------------------------------------------------------------

User uploads CSV
        |
        v
Dataset stored and loaded into DuckDB
        |
        v
Schema + stats inferred
        |
        v
User asks question in chat
        |
        v
Master Agent plans and selects tools
        |
        v
MCP agents run analysis on the dataset
        |
        v
Results + explanations returned to user

----------------------------------------------------------------
## ARCHITECTURE (ASCII DIAGRAM)
----------------------------------------------------------------

            +----------------------+
            |      Frontend        |
            |  (Web UI / Chat)     |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |   Backend API        |
            |   (FastAPI)          |
            |----------------------|
            | - Session handling   |
            | - Dataset registry   |
            | - Master Agent LLM   |
            | - MCP Client         |
            +----------+-----------+
                       |
      ------------------------------------------------
      |                |               |            |
      v                v               v            v
+-----------+    +-----------+   +-------------+  +-----------+
| SQL Agent |    | EDA Agent |   | Regression  |  | Plot Agent|
| (MCP)     |    | (MCP)     |   | Agent (MCP) |  | (MCP)     |
| SELECT    |    | Stats     |   | Models      |  | Charts    |
+-----+-----+    +-----+-----+   +------+------+  +-----+-----+
      \               |               |                  /
       \              |               |                 /
        -------------------------------------------------
                         |
                   +-----------+
                   | Data Layer|
                   |-----------|
                   | DuckDB    |
                   | CSV/Parq  |
                   +-----------+

----------------------------------------------------------------
## REPOSITORY STRUCTURE
----------------------------------------------------------------

omniagent/
│
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── api/                 # HTTP endpoints
│   ├── core/                # Config, logging, sessions
│   ├── data/                # CSV loading, schema, sampling
│   ├── agents/              # Master agent & planning logic
│   └── mcp/                 # MCP tool servers
│       ├── sql_server.py
│       ├── eda_server.py
│       ├── regression_server.py
│       └── plot_server.py
│
├── frontend/                # Web UI (optional / later)
├── tests/
├── environment.yml
├── conda-lock.yml
├── .env
└── README.md

----------------------------------------------------------------
## DESIGN PRINCIPLES
----------------------------------------------------------------

- One Master Agent orchestrates all actions
- Specialized agents do one task each
- No arbitrary code execution
- SQL is read-only (SELECT-only)
- Ambiguity triggers clarifying questions
- All results are explainable and transparent

----------------------------------------------------------------
## STATUS
----------------------------------------------------------------

Current focus:
- MVP with CSV upload, chat, SQL, EDA, plots, and regression
- Designed for future extension (time series, clustering, NLP)

----------------------------------------------------------------
