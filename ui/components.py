"""
UI Components Module
====================
Streamlit UI components for OmniAgent.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.config import Config, STYLES
from core.analyzer import DataAnalyzer
from core.llm import LLMClient
from agents.master_agent import MasterAgent


def init_page():
    """Initialize Streamlit page configuration."""
    st.set_page_config(
        page_title=Config.PAGE_TITLE,
        page_icon=Config.PAGE_ICON,
        layout=Config.LAYOUT,
        initial_sidebar_state="expanded"
    )
    st.markdown(STYLES, unsafe_allow_html=True)


def init_session():
    """Initialize session state variables."""
    defaults = {
        'messages': [],
        'df': None,
        'filename': None,
        'analyzer': None,
        'master': None,
        'llm': None,
        'ai_enabled': True,
        'api_key': Config.GROQ_API_KEY
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    
    if st.session_state.llm is None:
        st.session_state.llm = LLMClient(st.session_state.api_key)


def add_message(role: str, content: str, **kwargs):
    """Add a message to chat history."""
    st.session_state.messages.append({
        'role': role,
        'content': content,
        'figure': kwargs.get('figure'),
        'insights': kwargs.get('insights'),
        'suggestions': kwargs.get('suggestions'),
        'agent': kwargs.get('agent'),
        'emoji': kwargs.get('emoji'),
        'dataframe': kwargs.get('dataframe')
    })


def load_data(source, filename: str = None) -> bool:
    """Load data from file or path."""
    import pandas as pd
    
    try:
        if isinstance(source, (str, Path)):
            df = pd.read_csv(source)
            filename = Path(source).name
        else:
            df = pd.read_csv(source)
        
        st.session_state.df = df
        st.session_state.filename = filename
        st.session_state.analyzer = DataAnalyzer(df)
        st.session_state.master = MasterAgent(
            df, 
            st.session_state.analyzer,
            st.session_state.llm
        )
        return True
    except Exception as e:
        add_message('assistant', f"❌ Error loading data: {str(e)}")
        return False


def process_query(query: str):
    """Process user query through master agent."""
    if st.session_state.df is None:
        add_message('assistant', "Please load a dataset first!", suggestions=["Help"])
        return
    
    # Update LLM state
    if st.session_state.llm:
        st.session_state.llm.toggle(st.session_state.ai_enabled)
    
    # Process query
    result = st.session_state.master.process(query)
    
    # Handle special __HOME__ response (go to welcome)
    if result.get('content') == '__HOME__':
        st.session_state.messages = []
        return
    
    add_message(
        'assistant',
        result.get('content', ''),
        figure=result.get('figure'),
        insights=result.get('insights'),
        suggestions=result.get('suggestions'),
        agent=result.get('agent_name') or result.get('agent'),
        emoji=result.get('agent_emoji') or result.get('emoji'),
        dataframe=result.get('dataframe')
    )


def get_loaded_message() -> Dict[str, Any]:
    """Generate message for newly loaded data with 8 suggestions per category."""
    a = st.session_state.analyzer
    s = a.get_summary()
    
    missing_pct = (s['missing_total'] / (a.row_count * a.col_count) * 100) if a.row_count > 0 else 0
    
    # Numeric stats
    num_previews = []
    for col in a.usable_numeric[:4]:
        data = a.df[col].dropna()
        num_previews.append(f"  - **{col}**: μ={data.mean():.2f}, σ={data.std():.2f}")
    
    # Categorical stats
    cat_previews = []
    for col in a.usable_categorical[:4]:
        unique = a.df[col].nunique()
        cat_previews.append(f"  - **{col}**: {unique} categories")
    
    content = f"""## ✅ Data Successfully Loaded: {st.session_state.filename}

### 📊 Dataset Overview

| Property | Value | Description |
|----------|-------|-------------|
| **Rows** | {s['rows']:,} | Total observations |
| **Columns** | {s['columns']} | Total variables |
| **Numeric** | {len(s['numeric_columns'])} | Quantitative features |
| **Categorical** | {len(s['categorical_columns'])} | Qualitative features |
| **Missing** | {s['missing_total']:,} ({missing_pct:.1f}%) | Empty cells |
| **Memory** | {s['memory_mb']:.2f} MB | Dataset size |

---

### 🔢 Numeric Columns Preview

{chr(10).join(num_previews) if num_previews else 'No numeric columns'}

---

### 📝 Categorical Columns Preview

{chr(10).join(cat_previews) if cat_previews else 'No categorical columns'}"""
    
    if s['id_columns']:
        content += f"""

---

### 🔑 Auto-Detected ID Columns

**{', '.join(s['id_columns'])}**

*These columns will be automatically excluded from modeling.*"""
    
    if a.target_candidates:
        content += """

---

### 🎯 Suggested Prediction Targets

| Column | Type | Details |
|--------|------|---------|"""
        for c in a.target_candidates[:4]:
            detail = f"{c['classes']} classes" if c['type'] == 'classification' else "Continuous"
            content += f"\n| {c['column']} | {c['type'].title()} | {detail} |"
    
    content += """

---

### 🚀 Getting Started

Your data is ready! Here's what you can do:

1. **📊 Explore**: "Show statistics" or "Tell me about this dataset"

2. **📈 Visualize**: "Histogram of [column]" or "Correlation heatmap"

3. **📦 Aggregate**: "Count by [column]" or "Sum [num] by [cat]"

4. **🤖 Predict**: "Predict [column]" to build ML models

5. **🔍 Query**: "Show first 10 rows" or "Check missing values"

**Just type naturally - I understand many variations!**"""
    
    insights = f"""**📋 Data Summary:**

• **{s['rows']:,} rows** × **{s['columns']} columns** loaded successfully

• **{len(s['numeric_columns'])} numeric** features ready for analysis

• **{len(s['categorical_columns'])} categorical** features available

• {"✅ **Complete data** - no missing values!" if s['missing_total'] == 0 else f"⚠️ **{s['missing_total']:,} missing values** ({missing_pct:.1f}%) - will be handled automatically"}

• {"🔑 **ID columns detected**: " + ', '.join(s['id_columns']) + " (auto-excluded)" if s['id_columns'] else "No ID columns detected"}

• **Ready for exploration and modeling!**"""
    
    # Build 8 suggestions per category
    num = a.usable_numeric
    cat = a.usable_categorical
    targets = a.target_candidates
    
    suggestions = []
    
    # Stats (8)
    suggestions.extend([
        f"📊 Mean of {num[0]}" if num else "📊 Statistics",
        f"📊 Median of {num[0]}" if num else "📊 Median",
        f"📊 Std of {num[0]}" if num else "📊 Std deviation",
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
    suggestions.extend(["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"])
    
    return {'content': content, 'insights': insights, 'suggestions': suggestions}
