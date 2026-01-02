"""
Master Agent Module
===================
Central orchestrator using Message Communication Protocol (MCP).
Best-in-class agent routing and natural language understanding.
"""

import pandas as pd
import re
import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.base import BaseAgent
from agents.stats_agent import StatsAgent
from agents.viz_agent import VizAgent
from agents.predict_agent import PredictAgent
from agents.sql_agent import SQLAgent
from agents.aggregate_agent import AggregateAgent
from core.analyzer import DataAnalyzer
from core.config import Config
from core.llm import LLMClient
from mcp.protocol import MCPBus, MCPMessage, MessageType


class MasterAgent(BaseAgent):
    """
    Master Agent - Central Orchestrator
    ====================================
    Uses Message Communication Protocol (MCP) for best-in-class agent routing.
    
    Features:
    - Natural language understanding with 200+ patterns
    - Smart context-aware routing
    - Agent-specific suggestion generation (12 per agent)
    - Conversation flow management
    """
    
    name = "Master Agent"
    emoji = "🧠"
    description = "Central orchestrator for all agents"
    
    # Comprehensive patterns - ORDER MATTERS (most specific first)
    PATTERNS = {
        # Aggregate patterns (check FIRST - most specific)
        'aggregate': [
            'group by', 'groupby', 'grouped by', 'aggregate', 'aggregation',
            'pivot', 'pivot table', 'cross tab', 'crosstab', 'summarize by',
            'count by', 'count per', 'counts by', 'how many per', 'number per',
            'sum by', 'sum per', 'total by', 'total per', 'totals by',
            'average by', 'avg by', 'mean by', 'average per', 'avg per',
            'max by', 'maximum by', 'highest by', 'max per',
            'min by', 'minimum by', 'lowest by', 'min per',
            'per group', 'by group', 'for each', 'by each', 'breakdown by',
            'split by', 'segment by', 'partition by'
        ],
        
        # Predict patterns (check before stats - "model" keyword)
        'predict': [
            'predict', 'prediction', 'forecast', 'forecasting',
            'model', 'build model', 'create model', 'train model', 'make model',
            'machine learning', 'ml', 'ai model',
            'classify', 'classification', 'classifier',
            'regression', 'regressor',
            'can you predict', 'make predictions', 'predictive',
            'target variable', 'dependent variable',
            'supervised learning', 'train a', 'training',
            'feature importance', 'important features', 'what factors',
            'what influences', 'what affects', 'what drives'
        ],
        
        # Overview/Dataset Info patterns
        'overview': [
            'tell me about', 'about this data', 'about the data', 'about dataset',
            'data summary', 'dataset summary', 'summary of data', 'summarize data',
            'overview', 'data overview', 'dataset overview',
            'what is this', 'what data', 'what do we have', 'what am i looking at',
            'describe data', 'describe dataset', 'data description',
            'explain data', 'explain dataset', 'information about',
            'dataset info', 'data info', 'give me summary'
        ],
        
        # Stats patterns
        'stats': [
            'statistic', 'statistics', 'stats', 'stat',
            'describe', 'descriptive', 'summary statistics',
            'mean', 'average', 'avg', 'typical value',
            'median', 'middle value', '50th percentile',
            'std', 'standard deviation', 'deviation', 'spread', 'variability',
            'variance', 'var',
            'min', 'minimum', 'lowest', 'smallest',
            'max', 'maximum', 'highest', 'largest', 'biggest',
            'percentile', 'quartile', '25%', '50%', '75%', 'iqr',
            'range', 'span',
            'skew', 'skewness', 'kurtosis',
            'mode', 'most common',
            'how much', 'what is the average', 'what is the mean',
            'calculate', 'compute', 'find the value'
        ],
        
        # Missing values patterns
        'missing': [
            'missing', 'null', 'nan', 'na', 'n/a',
            'empty', 'blank', 'incomplete',
            'data quality', 'quality check', 'completeness',
            'gaps', 'holes', 'absent',
            'check for missing', 'find missing', 'any missing', 'are there missing'
        ],
        
        # Histogram patterns
        'histogram': [
            'histogram', 'histograms', 'hist',
            'distribution', 'distributions', 'dist',
            'frequency distribution', 'frequency chart',
            'bell curve', 'normal distribution',
            'shape of', 'spread of', 'how distributed'
        ],
        
        # Scatter plot patterns
        'scatter': [
            'scatter', 'scatter plot', 'scatterplot',
            'relationship between', 'relation between',
            'vs', 'versus', 'against', 'compared to',
            'x and y', 'xy plot', 'x vs y',
            'correlation between', 'how does x relate',
            'association', 'associated with'
        ],
        
        # Bar chart patterns
        'bar': [
            'bar chart', 'bar graph', 'barchart', 'bar plot',
            'count of', 'frequency of', 'counts for',
            'breakdown', 'by category'
        ],
        
        # Box plot patterns
        'box': [
            'box plot', 'boxplot', 'box and whisker',
            'outlier', 'outliers', 'find outliers', 'detect outliers',
            'anomaly', 'anomalies', 'extreme values',
            'iqr', 'interquartile', 'five number summary', 'quartile plot'
        ],
        
        # Heatmap patterns
        'heatmap': [
            'heatmap', 'heat map', 'correlation matrix',
            'correlation', 'correlations', 'corr',
            'all correlations', 'pairwise correlation',
            'relationships between all', 'multivariate'
        ],
        
        # Pie chart patterns
        'pie': [
            'pie chart', 'pie graph', 'pie plot',
            'proportion', 'proportions', 'percentage breakdown',
            'composition', 'share', 'slice'
        ],
        
        # All numeric patterns
        'all_numeric': [
            'all numeric', 'all numbers', 'all numerical',
            'every numeric', 'numeric overview',
            'all distributions', 'show all numeric'
        ],
        
        # All categorical patterns
        'all_categorical': [
            'all categorical', 'all categories', 'all text',
            'every category', 'categorical overview',
            'show all categorical'
        ],
        
        # Columns/Schema patterns
        'columns': [
            'columns', 'column', 'fields', 'field',
            'schema', 'structure', 'data structure',
            'variables', 'features', 'attributes',
            'what columns', 'list columns', 'show columns', 'column names',
            'what variables', 'column types', 'data types'
        ],
        
        # Sample/Preview patterns
        'sample': [
            'sample', 'samples', 'random sample',
            'first', 'head', 'top rows', 'first rows',
            'last', 'tail', 'bottom rows', 'last rows',
            'preview', 'show data', 'view data', 'see data',
            'rows', 'show rows', 'display data',
            'peek', 'glimpse', 'snapshot', 'look at data'
        ],
        
        # Help patterns
        'help': [
            'help', 'how to', 'what can', 'guide', 'tutorial',
            'commands', 'options', 'features', 'capabilities',
            '?', 'instructions', 'how do i', 'teach me', 'show me how'
        ],
        
        # Navigation patterns
        'home': ['home', 'start', 'main', 'beginning', 'welcome', 'reset', 'start over'],
        'about': ['about', 'about app', 'about omniagent', 'architecture', 'technology', 
                  'tech stack', 'how does it work', 'how it works', 'system info'],
        
        # Generic plot patterns (catch-all for viz)
        'plot': [
            'plot', 'chart', 'graph', 'visualize', 'visualization',
            'draw', 'display', 'show me', 'visual', 'figure', 'diagram'
        ]
    }
    
    # Advanced patterns that require Dynamic Agent (LLM code generation)
    # These are MORE SPECIFIC phrases that indicate complex analysis
    DYNAMIC_PATTERNS = [
        # Rolling/Window calculations (specific phrases)
        'rolling average', 'rolling mean', 'rolling sum',
        'moving average', 'moving avg', 'moving mean',
        'sliding window', 'window average',
        'cumulative sum', 'cumulative average', 'running total', 'running sum', 'running average',
        '3-day', '5-day', '7-day', '14-day', '30-day', '90-day',
        'weekly average', 'monthly average', 'daily average',
        
        # Statistical methods (specific phrases) - EXPANDED
        'z-score', 'z score', 'zscore', 'z-scores', 'zscores',  # Added standalone z-score patterns
        'using iqr', 'iqr method', 'using the iqr',
        'using z-score', 'z-score method', 'zscore method',
        'outliers using', 'detect outliers using', 'find outliers using',
        'outliers in', 'identify outliers',
        'anomaly detection', 'detect anomalies',
        'statistical test', 't-test', 'anova', 'chi-square', 'chi square',
        'shapiro', 'normality test', 'test for normality',
        'partial correlation', 'controlling for', 'control for',
        
        # Regression/Trend (specific phrases)
        'with regression', 'regression line', 'with a regression',
        'with trend', 'trend line', 'trendline', 'with a trend',
        'best fit line', 'line of best fit',
        'linear fit', 'polynomial fit', 'fitted line',
        'r-squared', 'r squared', 'coefficient of determination',
        
        # Feature engineering (specific phrases)
        'create a new column', 'create new column', 'add a column', 'add new column',
        'categorize into', 'bin into', 'bucket into',
        'bins', 'binning', 'discretize',
        'split into categories', 'group into categories',
        'based on percentile', 'percentile-based', 'quartile-based',
        'normalize the', 'standardize the', 'scale the',
        'normalize all', 'standardize all', 'normalize column', 'standardize column',  # Added
        
        # Clustering (specific phrases)
        'cluster the', 'clustering', 'k-means', 'kmeans',
        'dbscan', 'segment the data', 'segmentation',
        'group similar', 'find groups',
        
        # Time series (specific phrases)
        'time series decomposition', 'decompose',
        'seasonality', 'seasonal pattern',
        'year-over-year', 'yoy growth', 'month-over-month', 'mom growth',
        'growth rate', 'percent change', 'percentage change',
        'lag of', 'lagged', 'difference of',
        
        # Complex calculations (specific phrases)
        'ratio of', 'calculate ratio', 'calories to duration ratio',
        'per capita', 'weighted average', 'weighted mean',
        'top 10', 'top 5', 'top 20', 'bottom 10', 'bottom 5',
        'highest ratio', 'lowest ratio',
        'rank by', 'ranking of',
        
        # Specific complex requests
        'custom calculation', 'custom analysis',
        'advanced analysis', 'complex analysis',
    ]
    
    # Patterns that should be REFUSED (dangerous/not supported)
    REFUSE_PATTERNS = {
        'delete': "🚫 I can't delete or remove your data. Would you like to **filter** or **subset** it instead?",
        'remove all': "🚫 I can't remove data. Try asking to **filter** or **show rows where...**",
        'drop rows': "🚫 I can't drop rows from your data. Would you like to **filter** to specific rows instead?",
        'drop columns': "🚫 I can't drop columns. Would you like to **show specific columns** instead?",
        'download': "🚫 I can't download files. You can **copy** the results from the screen or take a screenshot.",
        'upload': "🚫 Use the **📂 Load Data** section in the sidebar to upload files.",
        'save to file': "🚫 I can't save files. You can **copy** results from the screen.",
        'export': "🚫 I can't export files directly. Copy the results you need from the display.",
        'hack': "🚫 I can't help with that. Let me know if you have a data analysis question!",
        'exploit': "🚫 I can't help with security exploits. Ask me about data analysis instead.",
        'inject': "🚫 I only do data analysis. What would you like to know about your data?",
        'password': "🚫 I don't handle passwords or credentials. Ask me about your data!",
        'credential': "🚫 I don't handle credentials. What data analysis can I help with?",
        'send email': "🚫 I can't send emails. I only analyze the data you've loaded.",
        'connect to': "🚫 I can't connect to external services. I work with the data you've uploaded.",
    }
    
    def __init__(self, df: pd.DataFrame, analyzer: DataAnalyzer, llm: LLMClient = None):
        super().__init__(df, analyzer)
        self.llm = llm
        self.current_agent = None
        self.conversation_context = []
        self.mcp_bus = MCPBus()
        self._init_agents()
    
    def _init_agents(self):
        """Initialize and register all agents with MCP bus."""
        # Create agent instances
        self.stats = StatsAgent(self.df, self.analyzer)
        self.viz = VizAgent(self.df, self.analyzer)
        self.predict = PredictAgent(self.df, self.analyzer)
        self.sql = SQLAgent(self.df, self.analyzer)
        self.aggregate = AggregateAgent(self.df, self.analyzer)
        
        # Register with MCP bus for message routing
        self.mcp_bus.register_agent('stats', self.stats)
        self.mcp_bus.register_agent('viz', self.viz)
        self.mcp_bus.register_agent('predict', self.predict)
        self.mcp_bus.register_agent('sql', self.sql)
        self.mcp_bus.register_agent('aggregate', self.aggregate)
        self.mcp_bus.register_agent('master', self)
    
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process user query using MCP routing.
        
        Flow:
        1. CHECK if Dynamic Agent has pending confirmation (handle yes/no)
        2. Detect intent from query
        3. Route to appropriate agent via MCP
        4. Return formatted response with suggestions
        """
        q = query.lower().strip()
        
        # FIRST: Check if Dynamic Agent is waiting for confirmation
        # This MUST be checked before any other routing
        if self._is_dynamic_pending():
            result = self._send_to_dynamic(query)
            result['agent'] = result.get('agent', "Dynamic Agent")
            result['emoji'] = result.get('emoji', "🔮")
            if 'suggestions' not in result or not result['suggestions']:
                result['suggestions'] = self._get_suggestions()
            return result
        
        # Log query for context
        self.conversation_context.append({
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
        # Detect intent
        intent = self._detect_intent(q)
        
        # Route to appropriate handler
        result = self._route(intent, q)
        
        # Ensure response format
        result['agent'] = result.get('agent', self.name)
        result['emoji'] = result.get('emoji', self.emoji)
        
        # Generate suggestions if not present
        if 'suggestions' not in result or not result['suggestions']:
            result['suggestions'] = self._get_suggestions()
        
        return result
    
    def _is_dynamic_pending(self) -> bool:
        """Check if Dynamic Agent has a pending confirmation."""
        if 'dynamic_state' not in st.session_state:
            return False
        state = st.session_state.dynamic_state
        return state in ['offered', 'planned']
    
    def _detect_intent(self, query: str) -> Optional[str]:
        """
        Detect user intent using pattern matching.
        Returns the most specific matching intent.
        """
        # FIRST: Check if this should be REFUSED
        for pattern in self.REFUSE_PATTERNS.keys():
            if pattern in query:
                return 'refuse'
        
        # SECOND: Check if query requires Dynamic Agent (advanced analysis)
        # These patterns indicate complex requests that built-in agents can't handle
        for pattern in self.DYNAMIC_PATTERNS:
            if pattern in query:
                return 'dynamic'
        
        # Check standard patterns in order (most specific first)
        for intent, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if pattern in query:
                    return intent
        
        # Fuzzy matching for question words
        if any(word in query for word in ['how', 'what', 'show', 'give', 'find', 'get', 'can you']):
            if any(word in query for word in ['column', 'variable', 'field']):
                return 'columns'
            if any(word in query for word in ['row', 'data', 'record']):
                return 'sample'
        
        return None
    
    def _route(self, intent: str, query: str) -> Dict:
        """Route query to appropriate agent via MCP message bus."""
        
        # REFUSE dangerous/unsupported requests
        if intent == 'refuse':
            return self._refuse_request(query)
        
        # Navigation handlers (no MCP needed)
        if intent == 'home':
            return {'content': '__HOME__', 'suggestions': []}
        
        if intent == 'about':
            self.current_agent = None
            return self._about()
        
        if intent == 'help':
            self.current_agent = None
            return self._help()
        
        if intent == 'overview':
            self.current_agent = 'master'
            return self._data_overview()
        
        # Dynamic Agent for advanced/complex queries
        if intent == 'dynamic':
            self.current_agent = 'dynamic'
            return self._send_to_dynamic(query)
        
        # MCP routing to specialized agents
        if intent == 'aggregate':
            self.current_agent = 'aggregate'
            return self._send_to_agent('aggregate', query)
        
        if intent == 'predict':
            self.current_agent = 'predict'
            return self._send_to_agent('predict', query)
        
        if intent in ['stats', 'missing']:
            self.current_agent = 'stats'
            return self._send_to_agent('stats', query)
        
        if intent in ['histogram', 'scatter', 'bar', 'box', 'heatmap', 'pie', 
                      'all_numeric', 'all_categorical', 'plot']:
            self.current_agent = 'viz'
            return self._send_to_agent('viz', query)
        
        if intent in ['columns', 'sample']:
            self.current_agent = 'sql'
            return self._send_to_agent('sql', query)
        
        # Unknown intent - try Dynamic Agent or provide guidance
        return self._unknown(query)
    
    def _refuse_request(self, query: str) -> Dict:
        """Refuse a dangerous or unsupported request with helpful message."""
        q = query.lower()
        
        # Find which refuse pattern matched
        message = "🚫 I can't help with that request."
        for pattern, msg in self.REFUSE_PATTERNS.items():
            if pattern in q:
                message = msg
                break
        
        return {
            'content': f"""## 🚫 Request Not Supported

{message}

### What I CAN do:
- 📊 **Statistics**: "Show statistics", "Mean of [column]"
- 📈 **Visualizations**: "Histogram of [column]", "Scatter plot"
- 📦 **Aggregations**: "Count by [category]", "Sum [value] by [group]"
- 🤖 **Predictions**: "Predict [column]", "Build model"
- 🔮 **Custom Analysis**: "Calculate rolling average", "Find outliers"

### Try one of the suggestions below!
""",
            'insights': "This request is not supported. Try a data analysis question instead.",
            'suggestions': self._get_home_suggestions()
        }
    
    def _send_to_agent(self, target: str, query: str) -> Dict:
        """Send message to agent via MCP bus and get response."""
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target=target,
            content=query,
            metadata={'timestamp': datetime.now().isoformat()}
        )
        
        response = self.mcp_bus.send(msg)
        
        if response:
            return response.to_dict()
        else:
            return self.format_error(f"Agent '{target}' failed to respond")
    
    def _send_to_dynamic(self, query: str) -> Dict:
        """Send query to Dynamic Agent for AI-powered analysis."""
        from agents.dynamic_agent import DynamicAgent
        
        dynamic_agent = DynamicAgent(analyzer=self.analyzer, llm=self.llm)
        result = dynamic_agent.process(query)
        
        # Add agent info
        result['agent'] = "Dynamic Agent"
        result['emoji'] = "🔮"
        
        return result
    
    def _data_overview(self) -> Dict[str, Any]:
        """Generate comprehensive dataset overview."""
        a = self.analyzer
        s = a.get_summary()
        missing_total = s['missing_total']
        missing_pct = (missing_total / (a.row_count * a.col_count) * 100) if a.row_count > 0 else 0
        
        # Determine data size category
        if a.row_count > 100000:
            size_cat = "very large"
        elif a.row_count > 10000:
            size_cat = "large"
        elif a.row_count > 1000:
            size_cat = "medium"
        else:
            size_cat = "small"
        
        content = f"""## 📋 Dataset Information

### 📊 Overview

| Property | Value | Interpretation |
|----------|-------|----------------|
| **Rows** | {a.row_count:,} | {size_cat.title()} dataset with {a.row_count:,} observations |
| **Columns** | {a.col_count} | {a.col_count} variables to analyze |
| **Numeric** | {len(a.usable_numeric)} | Quantitative features for statistics & modeling |
| **Categorical** | {len(a.usable_categorical)} | Qualitative features for grouping & filtering |
| **Missing** | {missing_total:,} ({missing_pct:.1f}%) | {"✅ Complete data!" if missing_total == 0 else "⚠️ Has missing values"} |
| **Memory** | {a.memory_usage:.2f} MB | Dataset size in memory |

---

### 🔢 Numeric Columns ({len(a.usable_numeric)})

"""
        for col in a.usable_numeric[:8]:
            data = self.df[col].dropna()
            content += f"• **{col}**: mean={data.mean():.2f}, std={data.std():.2f}, range=[{data.min():.2f}, {data.max():.2f}]\n"
        
        if len(a.usable_numeric) > 8:
            content += f"\n*...and {len(a.usable_numeric) - 8} more numeric columns*\n"
        
        content += f"""
---

### 📝 Categorical Columns ({len(a.usable_categorical)})

"""
        for col in a.usable_categorical[:6]:
            unique = self.df[col].nunique()
            top = self.df[col].value_counts().index[0] if len(self.df[col].value_counts()) > 0 else 'N/A'
            content += f"• **{col}**: {unique} unique values, most common: '{top}'\n"
        
        if a.id_columns:
            content += f"""
---

### 🔑 ID Columns (Auto-Excluded)

{', '.join(a.id_columns)}

*These are automatically excluded from modeling to prevent data leakage.*
"""
        
        content += """
---

### 🎯 What You Can Do Next

| Action | Command | Description |
|--------|---------|-------------|
| **Statistics** | "Show statistics" | Get descriptive stats for all columns |
| **Visualize** | "Histogram of [column]" | See data distributions |
| **Aggregate** | "Count by [column]" | Group and summarize data |
| **Predict** | "Predict [column]" | Build machine learning model |
| **Explore** | "Show first 10 rows" | Preview your data |
"""
        
        insights = f"""**💡 Dataset Analysis Summary:**

• You have a **{size_cat} dataset** with **{a.row_count:,} rows** and **{a.col_count} columns**

• **{len(a.usable_numeric)} numeric features** available for statistical analysis, correlations, and as model inputs

• **{len(a.usable_categorical)} categorical features** available for grouping, filtering, and as prediction targets

• {"✅ **Excellent data quality!** No missing values - ready for immediate analysis" if missing_total == 0 else f"⚠️ **{missing_total:,} missing values** detected ({missing_pct:.1f}%) - will be handled automatically during modeling"}

• **Recommended next steps:** Try "Show statistics" for an overview, "Correlation heatmap" to find relationships, or "Count by [category]" to explore distributions"""
        
        return {
            'content': content,
            'insights': insights,
            'suggestions': self._get_home_suggestions()
        }
    
    def _help(self) -> Dict[str, Any]:
        """Comprehensive help guide."""
        content = f"""## 🆘 Help Center - OmniAgent Guide

### 🎯 Quick Start

Just type what you want to know! I understand natural language.

---

### 🎤 Voice Assistant

**Talk to me!** Enable Voice in the sidebar for two-way conversation:

| Feature | How to Use |
|---------|------------|
| **Speak** | Click "Start Speaking" button, ask your question |
| **Listen** | I'll speak my responses back to you |
| **Settings** | Adjust voice speed and pitch in Voice Settings |

---

### 📊 Statistics Agent

**What it does:** Calculates statistics, analyzes distributions, checks data quality

**Example commands:**
| Command | What it does |
|---------|--------------|
| "Show statistics" | Descriptive stats for all columns |
| "Mean of price" | Average of a specific column |
| "Median of age" | Middle value of a column |
| "Check missing values" | Find incomplete data |
| "Describe salary" | Full stats for one column |
| "Standard deviation of sales" | Measure of spread |

---

### 📈 Visualization Agent

**What it does:** Creates interactive charts and plots

**Example commands:**
| Command | What it does |
|---------|--------------|
| "Histogram of age" | Distribution of a numeric column |
| "Bar chart of category" | Counts by category |
| "Scatter plot price vs quantity" | Relationship between two variables |
| "Correlation heatmap" | All pairwise correlations |
| "Box plot of salary" | Outliers and quartiles |
| "Show all numeric" | All distributions at once |

---

### 📦 Aggregation Agent

**What it does:** Groups data and calculates summaries

**Example commands:**
| Command | What it does |
|---------|--------------|
| "Count by gender" | Row counts per category |
| "Sum sales by region" | Totals per group |
| "Average price by category" | Means per group |
| "Group by status" | Summary statistics by group |
| "Max revenue by month" | Highest values per group |

---

### 🤖 Prediction Agent

**What it does:** Builds machine learning models

**Example commands:**
| Command | What it does |
|---------|--------------|
| "Predict churn" | Build classification model |
| "Build model" | Interactive model builder |
| "What can I predict?" | Suggested targets |
| "Feature importance" | Which variables matter |

---

### 🔍 SQL Agent

**What it does:** Explores and previews data

**Example commands:**
| Command | What it does |
|---------|--------------|
| "Show first 10 rows" | Preview data |
| "Show columns" | List all columns |
| "Random sample" | Random rows |
| "Data structure" | Schema info |

---

### 💡 Pro Tips

1. **Be specific** - "Mean of price" works better than just "mean"
2. **Use column names** - I understand your actual column names
3. **Click suggestions** - Quick actions are always available
4. **Try aggregations** - "Sum sales by region" gives powerful insights
5. **Build models** - "Predict [column]" creates ML models automatically
6. **Use voice** - Enable Voice in sidebar to speak your questions!
7. **Enable AI** - Get dynamic analysis for any question!

---

### 🔮 Dynamic Agent (AI Mode)

With **AI Mode** enabled, I can create custom analysis for **any question**:

**Three-Step Flow (Resource Efficient):**
1. **Step 1:** I'll offer to create the analysis (no AI call yet)
2. **Step 2:** Type `yes` → I generate the plan and code
3. **Step 3:** Type `yes` → I execute and show results

**Example commands:**
| Command | What it does |
|---------|--------------|
| "Calculate rolling average" | Time-window calculations |
| "Find outliers using IQR" | Statistical outlier detection |
| "Create bins for age" | Categorize continuous data |
| "Scatter with regression line" | Trend visualization |
| "Top 10 by ratio" | Ranking calculations |

**Enable:** 🧠 AI Assistant in sidebar → Add Groq API key
"""
        
        return {
            'content': content,
            'insights': "**💡 Tip:** I understand many ways to ask the same thing. Just describe what you want to know about your data!",
            'suggestions': self._get_home_suggestions()
        }
    
    def _about(self) -> Dict[str, Any]:
        """About page with architecture and technology."""
        content = f"""## ℹ️ About OmniAgent

### 🎯 What is OmniAgent?

OmniAgent is an **AI-powered multi-agent data analysis system** that helps you explore, visualize, and understand your data through natural conversation.

---

### 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                             │                                   │
│                             ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    🧠 MASTER AGENT                         │ │
│  │                                                            │ │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │ │
│  │   │   Intent    │───▶│   Router    │───▶│     MCP     │  │ │
│  │   │  Detection  │    │   Logic     │    │   Message   │  │ │
│  │   └─────────────┘    └─────────────┘    │     Bus     │  │ │
│  │                                          └──────┬──────┘  │ │
│  └─────────────────────────────────────────────────┼─────────┘ │
│                                                    │            │
│     ┌──────────┬──────────┬──────────┬──────────┬─┴────────┐  │
│     ▼          ▼          ▼          ▼          ▼          ▼  │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │
│  │  📊  │  │  📈  │  │  📦  │  │  🤖  │  │  🔍  │  │  🔮  │  │
│  │Stats │  │ Viz  │  │ Agg  │  │Pred  │  │ SQL  │  │Dynamic│  │
│  │Agent │  │Agent │  │Agent │  │Agent │  │Agent │  │Agent │  │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  │
│                                                    │           │
│                              ┌─────────────────────┘           │
│                              ▼                                 │
│                    ┌─────────────────┐                         │
│                    │  FORMATTED      │                         │
│                    │  RESPONSE +     │                         │
│                    │  SUGGESTIONS    │                         │
│                    └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

### 📡 Message Communication Protocol (MCP)

OmniAgent uses **MCP** for best-in-class agent communication:

```python
# Message Structure
MCPMessage(
    id: str,           # Unique message ID
    type: MessageType, # QUERY, RESPONSE, ERROR
    source: str,       # Sending agent
    target: str,       # Receiving agent  
    content: str,      # Message content
    data: dict,        # Additional data
    metadata: dict     # Timestamps, context
)
```

**MCP Features:**
• **Typed Messages** - Query, Response, Error, Event types
• **Message Bus** - Central routing hub
• **Agent Registry** - Dynamic agent registration
• **Response Wrapping** - Standardized responses

---

### 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit | Interactive web UI |
| **Visualization** | Plotly | Interactive charts |
| **Data** | Pandas, NumPy | Data processing |
| **ML** | Scikit-learn | Predictive models |
| **AI/NLU** | Groq (LLaMA 3.3 70B) | Natural language |
| **Architecture** | MCP | Agent communication |

---

### 🤖 Agent Capabilities

| Agent | Capabilities | Patterns Recognized |
|-------|--------------|---------------------|
| 📊 Stats | Mean, median, std, percentiles, missing | 30+ patterns |
| 📈 Viz | Histogram, scatter, bar, box, heatmap | 25+ patterns |
| 📦 Aggregate | GroupBy, count, sum, avg, pivot | 20+ patterns |
| 🤖 Predict | Classification, regression, feature importance | 20+ patterns |
| 🔍 SQL | Preview, schema, sampling | 15+ patterns |
| 🔮 Dynamic | Custom analysis via AI code generation | Any request |

---

### 🔮 Dynamic Agent (AI-Powered)

When you ask something beyond built-in capabilities, the **Dynamic Agent** creates custom analysis:

**Three-Step Flow:**
1. **Offer** - "I can create this! Want me to?" (saves resources if you cancel)
2. **Plan** - Shows generated code for review
3. **Execute** - Runs code safely and shows results

**Example requests:**
- "Calculate rolling 7-day average"
- "Find outliers using IQR method"
- "Create bins for age into categories"
- "Show scatter plot with regression line"

*Requires AI Mode enabled (Groq API key)*

---

### 👨‍💻 Created By

**{Config.AUTHOR}**

🌐 Website: [{Config.AUTHOR_URL}]({Config.AUTHOR_URL})

---

*Type "Help" for usage guide or "Dataset Info" for data overview*
"""
        
        return {
            'content': content,
            'insights': "**💡 OmniAgent** uses a multi-agent architecture with MCP (Message Communication Protocol) for best-in-class agent communication and routing.",
            'suggestions': self._get_home_suggestions()
        }
    
    def _unknown(self, query: str) -> Dict[str, Any]:
        """Handle unknown queries with Dynamic Agent or helpful guidance."""
        # Try Dynamic Agent if LLM is available
        if self.llm and self.llm.is_active():
            from agents.dynamic_agent import DynamicAgent
            dynamic_agent = DynamicAgent(analyzer=self.analyzer, llm=self.llm)
            result = dynamic_agent.process(query)
            
            # If dynamic agent succeeded, return its result
            if result and 'Dynamic Analysis' in result.get('content', ''):
                return result
            
            # Otherwise try simple LLM understanding
            context = f"""Dataset: {self.analyzer.row_count} rows, {self.analyzer.col_count} cols
Numeric: {', '.join(self.analyzer.usable_numeric[:5])}
Categorical: {', '.join(self.analyzer.usable_categorical[:5])}
Targets: {', '.join([t['column'] for t in self.analyzer.target_candidates[:3]])}"""
            
            response = self.llm.understand_query(query, context)
            if response:
                return {
                    'content': f"## 🧠 AI Response\n\n{response}",
                    'insights': "**💡 AI-powered response** - Try the suggestions below for more specific analysis!",
                    'suggestions': self._get_home_suggestions()
                }
        
        content = f"""## 🧠 Let Me Help You

I'm not sure how to handle: **"{query}"**

### 🔮 Enable AI for Dynamic Analysis

With AI Mode enabled, I can create **custom analysis** for any question!

**Examples of what I can do with AI:**
- "Calculate the 7-day rolling average"
- "Find outliers using IQR method"
- "Show the trend over time"
- "Calculate correlation controlling for a variable"

**Enable AI:** 🧠 AI Assistant in sidebar → Add Groq API key

---

### 💡 Built-in Commands (No AI Needed):

| Category | Try Saying |
|----------|------------|
| **Statistics** | "Show statistics", "Mean of [column]", "Check missing" |
| **Visualization** | "Histogram of [column]", "Correlation heatmap" |
| **Aggregation** | "Count by [column]", "Sum [number] by [category]" |
| **Prediction** | "Predict [column]", "Build model" |
| **Exploration** | "Show first 10 rows", "Show columns" |

### 📋 Your Columns

**Numeric:** {', '.join(self.analyzer.usable_numeric[:5])}

**Categorical:** {', '.join(self.analyzer.usable_categorical[:5])}
"""
        
        return {
            'content': content,
            'insights': "💡 Enable AI Mode for dynamic analysis capabilities!",
            'suggestions': self._get_home_suggestions()
        }
    
    def _get_suggestions(self) -> List[str]:
        """Get 12 context-aware suggestions based on current agent."""
        num = self.analyzer.usable_numeric
        cat = self.analyzer.usable_categorical
        targets = self.analyzer.target_candidates
        
        if self.current_agent == 'stats':
            sug = [
                f"Mean of {num[0]}" if num else "Show statistics",
                f"Median of {num[0]}" if num else "Check missing",
                f"Std of {num[0]}" if num else "Data quality",
                "Check missing values",
                f"Describe {num[1] if len(num) > 1 else num[0]}" if num else "Summary",
                f"Min of {num[0]}" if num else "Minimum",
                f"Max of {num[0]}" if num else "Maximum",
                "Show all statistics",
                f"25th percentile of {num[0]}" if num else "Percentiles",
                f"Range of {num[0]}" if num else "Range",
                "Data quality check",
                f"Variance of {num[0]}" if num else "Variance"
            ]
        elif self.current_agent == 'viz':
            sug = [
                f"Histogram of {num[0]}" if num else "Distribution",
                f"Box plot of {num[0]}" if num else "Outliers",
                f"Bar chart of {cat[0]}" if cat else "Bar chart",
                "Correlation heatmap",
                f"Scatter {num[0]} vs {num[1]}" if len(num) > 1 else "Scatter plot",
                f"Pie chart of {cat[0]}" if cat else "Pie chart",
                "Show all numeric",
                "Show all categorical",
                f"Histogram of {num[1]}" if len(num) > 1 else "Another histogram",
                f"Box plot of {num[1]}" if len(num) > 1 else "Another box plot",
                f"Bar chart of {cat[1]}" if len(cat) > 1 else "Another bar chart",
                "Distribution overview"
            ]
        elif self.current_agent == 'aggregate':
            sug = [
                f"Count by {cat[0]}" if cat else "Count by category",
                f"Group by {cat[0]}" if cat else "Group by",
                f"Sum {num[0]} by {cat[0]}" if num and cat else "Sum by group",
                f"Average {num[0]} by {cat[0]}" if num and cat else "Average by group",
                f"Max {num[0]} by {cat[0]}" if num and cat else "Max by group",
                f"Min {num[0]} by {cat[0]}" if num and cat else "Min by group",
                f"Count by {cat[1]}" if len(cat) > 1 else "Another count",
                f"Sum {num[1]} by {cat[0]}" if len(num) > 1 and cat else "Another sum",
                "Pivot table",
                "Group summary",
                "Aggregate overview",
                "Cross tabulation"
            ]
        elif self.current_agent == 'predict':
            sug = []
            for t in targets[:4]:
                sug.append(f"Predict {t['column']}")
            while len(sug) < 4:
                sug.append("What can I predict?")
            sug.extend([
                "Build model",
                "Feature importance",
                "ML overview",
                "Model suggestions",
                "Classification help",
                "Regression help",
                "Show statistics",
                "Correlation heatmap"
            ])
            sug = sug[:12]
        elif self.current_agent == 'sql':
            sug = [
                "Show first 10 rows",
                "Show first 20 rows",
                "Show first 50 rows",
                "Show last 10 rows",
                "Show random 15 rows",
                "Show random 30 rows",
                "Show columns",
                "Data structure",
                "Column types",
                "Show schema",
                "Preview data",
                "Data overview"
            ]
        else:
            return self._get_home_suggestions()
        
        # Navigation (always 4)
        nav = ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
        return sug[:12] + nav
    
    def _get_home_suggestions(self) -> List[str]:
        """Get categorized suggestions for home/overview (8 per category)."""
        num = self.analyzer.usable_numeric
        cat = self.analyzer.usable_categorical
        targets = self.analyzer.target_candidates
        
        suggestions = []
        
        # Stats (8)
        suggestions.extend([
            f"📊 Mean of {num[0]}" if num else "📊 Statistics",
            f"📊 Median of {num[0]}" if num else "📊 Check missing",
            f"📊 Std of {num[0]}" if num else "📊 Standard deviation",
            "📊 Check missing",
            "📊 Show statistics",
            "📊 Data quality",
            f"📊 Describe {num[0]}" if num else "📊 Describe",
            "📊 All statistics"
        ])
        
        # Viz (8)
        suggestions.extend([
            f"📈 Histogram of {num[0]}" if num else "📈 Histogram",
            f"📈 Bar chart of {cat[0]}" if cat else "📈 Bar chart",
            "📈 Correlation heatmap",
            "📈 Show all numeric",
            f"📈 Box plot of {num[0]}" if num else "📈 Box plot",
            f"📈 Scatter plot" if len(num) > 1 else "📈 Scatter",
            f"📈 Pie chart of {cat[0]}" if cat else "📈 Pie chart",
            "📈 Show all categorical"
        ])
        
        # Aggregate (8)
        suggestions.extend([
            f"📦 Count by {cat[0]}" if cat else "📦 Count by",
            f"📦 Sum {num[0]} by {cat[0]}" if num and cat else "📦 Sum by",
            f"📦 Average by {cat[0]}" if cat else "📦 Average by",
            f"📦 Group by {cat[0]}" if cat else "📦 Group by",
            f"📦 Max by {cat[0]}" if cat else "📦 Max by",
            f"📦 Min by {cat[0]}" if cat else "📦 Min by",
            "📦 Aggregation guide",
            "📦 Pivot table"
        ])
        
        # Predict (8)
        pred_sug = []
        for t in targets[:3]:
            pred_sug.append(f"🤖 Predict {t['column']}")
        while len(pred_sug) < 3:
            pred_sug.append("🤖 What can I predict?")
        pred_sug.extend([
            "🤖 Build model",
            "🤖 Feature importance",
            "🤖 ML overview",
            "🤖 Classification",
            "🤖 Regression"
        ])
        suggestions.extend(pred_sug[:8])
        
        # SQL (8)
        suggestions.extend([
            "🔍 First 10 rows",
            "🔍 First 20 rows",
            "🔍 Last 10 rows",
            "🔍 Random sample",
            "🔍 Show columns",
            "🔍 Data structure",
            "🔍 Column types",
            "🔍 Preview data"
        ])
        
        # Navigation (4)
        nav = ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
        
        return suggestions + nav
