"""
🤖 OmniAgent v3 - Guided Data Analysis Assistant
=================================================
A conversational, step-by-step data analysis experience.
Designed for non-technical users who want to explore data easily.

Run: streamlit run app_guided.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import os
from typing import Optional, Tuple, List, Dict, Any

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="🤖 OmniAgent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for chat interface and auto-scroll
st.markdown("""
<style>
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Chat container */
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding-bottom: 100px;
    }
    
    /* Message bubbles */
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        text-align: right;
    }
    
    .bot-msg {
        background: #f0f2f6;
        color: #1f1f1f;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 85%;
    }
    
    /* Option buttons in chat */
    .option-btn {
        display: inline-block;
        background: white;
        border: 2px solid #667eea;
        color: #667eea;
        padding: 8px 16px;
        border-radius: 20px;
        margin: 4px;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s;
    }
    
    .option-btn:hover {
        background: #667eea;
        color: white;
    }
    
    /* Data preview box */
    .data-preview {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Welcome header */
    .welcome-header {
        text-align: center;
        padding: 40px 20px;
    }
    
    .welcome-header h1 {
        font-size: 2.5rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Sidebar minimal */
    .sidebar-content {
        padding: 10px;
    }
    
    /* Auto-scroll script placeholder */
    .scroll-anchor {
        height: 1px;
    }
</style>

<script>
    // Auto-scroll to bottom
    function scrollToBottom() {
        window.scrollTo(0, document.body.scrollHeight);
    }
    setTimeout(scrollToBottom, 100);
</script>
""", unsafe_allow_html=True)


# ============================================================================
# LLM CLIENT (Optional)
# ============================================================================
class GroqClient:
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def chat(self, messages: List[Dict]) -> Optional[str]:
        import requests
        try:
            response = requests.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages, "temperature": 0.1, "max_tokens": 1024},
                timeout=30
            )
            if response.status_code == 429:
                return None
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except:
            return None


# ============================================================================
# DATA ANALYSIS FUNCTIONS
# ============================================================================
def get_data_summary(df: pd.DataFrame) -> Dict:
    """Get a simple summary of the data."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "numeric_columns": numeric_cols,
        "categorical_columns": cat_cols,
        "all_columns": df.columns.tolist(),
        "missing_total": int(df.isnull().sum().sum()),
        "sample_values": {col: df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else "N/A" 
                         for col in df.columns[:5]}
    }


def get_statistics(df: pd.DataFrame, column: str = None) -> str:
    """Get descriptive statistics."""
    if column and column in df.columns:
        stats = df[column].describe()
        result = f"**📊 Statistics for {column}:**\n\n"
        result += "| Metric | Value |\n|--------|-------|\n"
        for idx, val in stats.items():
            result += f"| {idx} | {val:.2f} |\n"
        return result
    else:
        # Create a nice formatted table for all numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return "No numeric columns found."
        
        stats = numeric_df.describe().round(2)
        
        result = "**📊 Overall Statistics:**\n\n"
        result += "| Column | Count | Mean | Std | Min | Max |\n"
        result += "|--------|-------|------|-----|-----|-----|\n"
        
        for col in stats.columns:
            result += f"| {col} | {stats[col]['count']:.0f} | {stats[col]['mean']:.2f} | {stats[col]['std']:.2f} | {stats[col]['min']:.2f} | {stats[col]['max']:.2f} |\n"
        
        return result


def get_missing_values(df: pd.DataFrame) -> str:
    """Get missing value report."""
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    
    result = "**Missing Values Report:**\n\n"
    has_missing = False
    for col in df.columns:
        if missing[col] > 0:
            has_missing = True
            result += f"• **{col}**: {missing[col]} ({missing_pct[col]}%)\n"
    
    if not has_missing:
        result += "✅ No missing values found! Your data is complete."
    
    return result


def get_outliers(df: pd.DataFrame, column: str) -> Tuple[str, Any]:
    """Detect outliers and create visualization."""
    if column not in df.columns:
        return f"Column '{column}' not found.", None
    
    data = df[column].dropna()
    if not np.issubdtype(data.dtype, np.number):
        return f"'{column}' is not numeric. Please choose a numeric column.", None
    
    Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
    IQR = Q3 - Q1
    lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
    outliers = data[(data < lower) | (data > upper)]
    
    # Create box plot
    fig = px.box(df, y=column, title=f"📦 Outlier Detection: {column}",
                 template="plotly_white")
    fig.add_hline(y=lower, line_dash="dash", line_color="red", 
                  annotation_text=f"Lower bound: {lower:.2f}")
    fig.add_hline(y=upper, line_dash="dash", line_color="red",
                  annotation_text=f"Upper bound: {upper:.2f}")
    
    text = f"""**Outlier Analysis for {column}:**

• **Method**: IQR (Interquartile Range)
• **Lower bound**: {lower:.2f}
• **Upper bound**: {upper:.2f}
• **Outliers found**: {len(outliers)} ({len(outliers)/len(data)*100:.1f}% of data)

{"⚠️ Some outliers detected! These might need investigation." if len(outliers) > 0 else "✅ No significant outliers found!"}"""
    
    return text, fig


def create_histogram(df: pd.DataFrame, column: str) -> Tuple[str, Any]:
    """Create histogram."""
    if column not in df.columns:
        return f"Column '{column}' not found.", None
    
    fig = px.histogram(df, x=column, title=f"📊 Distribution of {column}",
                       template="plotly_white", color_discrete_sequence=["#667eea"])
    fig.update_layout(bargap=0.1, showlegend=False)
    
    # Add statistics
    data = df[column].dropna()
    if np.issubdtype(data.dtype, np.number):
        text = f"""**Distribution of {column}:**

• **Mean**: {data.mean():.2f}
• **Median**: {data.median():.2f}
• **Std Dev**: {data.std():.2f}
• **Min**: {data.min():.2f}
• **Max**: {data.max():.2f}"""
    else:
        top_values = data.value_counts().head(3)
        text = f"""**Distribution of {column}:**

• **Unique values**: {data.nunique()}
• **Most common**: {top_values.index[0]} ({top_values.iloc[0]} times)"""
    
    return text, fig


def create_scatter(df: pd.DataFrame, x: str, y: str) -> Tuple[str, Any]:
    """Create scatter plot with trendline."""
    if x not in df.columns or y not in df.columns:
        return "One or both columns not found.", None
    
    fig = px.scatter(df, x=x, y=y, title=f"📈 Relationship: {x} vs {y}",
                     template="plotly_white", trendline="ols",
                     color_discrete_sequence=["#667eea"])
    
    # Calculate correlation
    corr = df[x].corr(df[y])
    
    text = f"""**Scatter Plot: {x} vs {y}**

• **Correlation**: {corr:.3f}
• **Interpretation**: {"Strong positive" if corr > 0.7 else "Strong negative" if corr < -0.7 else "Moderate positive" if corr > 0.3 else "Moderate negative" if corr < -0.3 else "Weak"} relationship

{"📈 These variables tend to increase together." if corr > 0.3 else "📉 These variables tend to move in opposite directions." if corr < -0.3 else "➡️ These variables don't have a strong relationship."}"""
    
    return text, fig


def create_bar_chart(df: pd.DataFrame, column: str) -> Tuple[str, Any]:
    """Create bar chart."""
    if column not in df.columns:
        return f"Column '{column}' not found.", None
    
    counts = df[column].value_counts().head(10)
    
    fig = px.bar(x=counts.index, y=counts.values, 
                 title=f"📊 Count by {column}",
                 template="plotly_white",
                 color_discrete_sequence=["#764ba2"])
    fig.update_layout(xaxis_title=column, yaxis_title="Count")
    
    text = f"""**Bar Chart: {column}**

• **Categories shown**: {len(counts)}
• **Most common**: {counts.index[0]} ({counts.iloc[0]} occurrences)
• **Least common**: {counts.index[-1]} ({counts.iloc[-1]} occurrences)"""
    
    return text, fig


def create_heatmap(df: pd.DataFrame) -> Tuple[str, Any]:
    """Create correlation heatmap."""
    numeric_df = df.select_dtypes(include=[np.number])
    
    if len(numeric_df.columns) < 2:
        return "Need at least 2 numeric columns for correlation heatmap.", None
    
    corr = numeric_df.corr()
    
    fig = px.imshow(corr, title="🔥 Correlation Heatmap",
                    color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                    template="plotly_white", text_auto=".2f")
    fig.update_layout(width=700, height=600)
    
    # Find strongest correlations
    strong_corrs = []
    for i in range(len(corr.columns)):
        for j in range(i+1, len(corr.columns)):
            val = corr.iloc[i, j]
            if abs(val) > 0.5:
                strong_corrs.append((corr.columns[i], corr.columns[j], val))
    
    strong_corrs.sort(key=lambda x: abs(x[2]), reverse=True)
    
    text = "**Correlation Heatmap**\n\n"
    if strong_corrs:
        text += "**Strong correlations found:**\n"
        for c1, c2, val in strong_corrs[:5]:
            direction = "↑↑" if val > 0 else "↑↓"
            text += f"• {c1} & {c2}: {val:.2f} {direction}\n"
    else:
        text += "No strong correlations found between variables."
    
    return text, fig


def create_pie_chart(df: pd.DataFrame, column: str) -> Tuple[str, Any]:
    """Create pie chart."""
    if column not in df.columns:
        return f"Column '{column}' not found.", None
    
    counts = df[column].value_counts().head(8)
    
    fig = px.pie(values=counts.values, names=counts.index,
                 title=f"🥧 Distribution of {column}",
                 template="plotly_white")
    
    text = f"""**Pie Chart: {column}**

• **Largest segment**: {counts.index[0]} ({counts.iloc[0]/counts.sum()*100:.1f}%)
• **Categories**: {len(counts)}"""
    
    return text, fig


def train_prediction_model(df: pd.DataFrame, target: str, features: List[str] = None) -> Tuple[str, Any]:
    """Train a simple prediction model."""
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score, mean_absolute_error
    
    if target not in df.columns:
        return f"Target column '{target}' not found.", None
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if target not in numeric_cols:
        return f"Target '{target}' must be numeric for prediction.", None
    
    # Auto-select features
    if not features:
        features = [c for c in numeric_cols if c != target][:5]
    
    if len(features) == 0:
        return "No features available for prediction.", None
    
    # Prepare data
    X = df[features].dropna()
    y = df.loc[X.index, target].dropna()
    X = X.loc[y.index]
    
    if len(X) < 30:
        return "Not enough data for reliable prediction (need 30+ rows).", None
    
    # Split and train
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    # Feature importance plot
    importance = pd.DataFrame({
        'Feature': features,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=True)
    
    fig = px.bar(importance, x='Importance', y='Feature', orientation='h',
                 title=f"🎯 Feature Importance for Predicting {target}",
                 template="plotly_white", color_discrete_sequence=["#667eea"])
    
    # Performance interpretation
    if r2 > 0.8:
        quality = "🌟 Excellent"
        advice = "The model can predict quite accurately!"
    elif r2 > 0.6:
        quality = "✅ Good"
        advice = "The model captures the main patterns."
    elif r2 > 0.3:
        quality = "⚠️ Moderate"
        advice = "Some patterns found, but predictions may vary."
    else:
        quality = "❌ Poor"
        advice = "The features don't explain the target well."
    
    text = f"""**🤖 Prediction Model for {target}**

**Model Performance:**
• **R² Score**: {r2:.3f} ({quality})
• **Mean Error**: {mae:.2f}
• **Training samples**: {len(X_train)}
• **Test samples**: {len(X_test)}

**Features used**: {', '.join(features)}

**What this means:** {advice}

**Most important features:**
1. {importance.iloc[-1]['Feature']} ({importance.iloc[-1]['Importance']:.1%})
2. {importance.iloc[-2]['Feature']} ({importance.iloc[-2]['Importance']:.1%})
"""
    
    return text, fig


# ============================================================================
# CONVERSATION STATE MACHINE
# ============================================================================
class ConversationState:
    WELCOME = "welcome"
    DATA_SELECTION = "data_selection"
    DATA_LOADED = "data_loaded"
    EXPLORING = "exploring"
    VISUALIZING = "visualizing"
    PREDICTING = "predicting"


# ============================================================================
# GUIDED RESPONSES
# ============================================================================
def get_welcome_message() -> str:
    return """# 👋 Welcome to OmniAgent!

I'm your **AI Data Analysis Assistant**. I'll help you explore and understand your data step by step - no coding required!

**Here's what I can do:**
• 📊 **Explore** your data with statistics and summaries
• 📈 **Visualize** patterns with interactive charts
• 🔍 **Find** missing values and outliers
• 🤖 **Predict** outcomes using machine learning

**Let's get started! How would you like to begin?**"""


def get_data_options() -> List[Dict]:
    return [
        {"label": "📂 Upload my own CSV file", "action": "upload"},
        {"label": "🏋️ Try Fitness Tracker sample", "action": "sample_fitness"},
        {"label": "🏠 Try NYC Airbnb sample", "action": "sample_airbnb"},
        {"label": "🛒 Try E-commerce Sales sample", "action": "sample_ecommerce"},
    ]


def get_data_loaded_message(summary: Dict, filename: str) -> str:
    return f"""# ✅ Data Loaded: {filename}

**Here's what I found:**

| Metric | Value |
|--------|-------|
| 📝 Rows | {summary['rows']:,} |
| 📊 Columns | {summary['columns']} |
| 🔢 Numeric columns | {len(summary['numeric_columns'])} |
| 📝 Text columns | {len(summary['categorical_columns'])} |
| ❓ Missing values | {summary['missing_total']:,} |

**Your columns:** {', '.join(summary['all_columns'][:8])}{'...' if len(summary['all_columns']) > 8 else ''}

**What would you like to do?**"""


def get_exploration_options(summary: Dict) -> List[Dict]:
    options = [
        {"label": "📊 Show statistics summary", "action": "stats"},
        {"label": "🔍 Check for missing values", "action": "missing"},
        {"label": "🔥 Show correlation heatmap", "action": "heatmap"},
    ]
    
    if summary['numeric_columns']:
        options.append({"label": f"📈 Histogram of {summary['numeric_columns'][0]}", 
                       "action": f"histogram_{summary['numeric_columns'][0]}"})
    
    if len(summary['numeric_columns']) >= 2:
        options.append({"label": f"🎯 Find outliers in {summary['numeric_columns'][0]}", 
                       "action": f"outliers_{summary['numeric_columns'][0]}"})
    
    if summary['categorical_columns']:
        options.append({"label": f"📊 Bar chart of {summary['categorical_columns'][0]}", 
                       "action": f"bar_{summary['categorical_columns'][0]}"})
    
    options.append({"label": "🤖 Build a prediction model", "action": "predict_start"})
    options.append({"label": "💬 Ask something else...", "action": "free_input"})
    
    return options


def get_visualization_options(summary: Dict) -> List[Dict]:
    options = []
    
    for col in summary['numeric_columns'][:4]:
        options.append({"label": f"📈 Histogram: {col}", "action": f"histogram_{col}"})
    
    for col in summary['categorical_columns'][:3]:
        options.append({"label": f"📊 Bar chart: {col}", "action": f"bar_{col}"})
    
    if len(summary['numeric_columns']) >= 2:
        x, y = summary['numeric_columns'][0], summary['numeric_columns'][1]
        options.append({"label": f"📈 Scatter: {x} vs {y}", "action": f"scatter_{x}_{y}"})
    
    options.append({"label": "🔥 Correlation heatmap", "action": "heatmap"})
    options.append({"label": "⬅️ Back to main options", "action": "back"})
    
    return options


def get_prediction_options(summary: Dict) -> List[Dict]:
    options = []
    for col in summary['numeric_columns'][:5]:
        options.append({"label": f"🎯 Predict {col}", "action": f"predict_{col}"})
    options.append({"label": "⬅️ Back to main options", "action": "back"})
    return options


def get_after_action_message() -> str:
    return "\n\n**What would you like to do next?**"


def get_after_action_options(summary: Dict) -> List[Dict]:
    return [
        {"label": "📊 More visualizations", "action": "viz_menu"},
        {"label": "🤖 Build prediction model", "action": "predict_start"},
        {"label": "📋 Show statistics", "action": "stats"},
        {"label": "🔍 Find outliers", "action": "outliers_menu"},
        {"label": "📂 Load different data", "action": "new_data"},
    ]


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
def init_session():
    defaults = {
        "messages": [],
        "df": None,
        "filename": None,
        "summary": None,
        "state": ConversationState.WELCOME,
        "pending_options": None,
        "use_llm": False,
        "llm_client": None,
        "show_upload": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    
    # Initialize LLM if key exists
    api_key = os.getenv("GROQ_API_KEY")
    if api_key and not st.session_state.llm_client:
        st.session_state.llm_client = GroqClient(api_key)


def add_message(role: str, content: str, options: List[Dict] = None, figure: Any = None):
    """Add message to chat history."""
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "options": options,
        "figure": figure
    })


def load_data(source, filename: str = None):
    """Load data into session."""
    try:
        if isinstance(source, (str, Path)):
            df = pd.read_csv(source)
            filename = Path(source).name
        else:
            df = pd.read_csv(source)
        
        st.session_state.df = df
        st.session_state.filename = filename
        st.session_state.summary = get_data_summary(df)
        st.session_state.state = ConversationState.DATA_LOADED
        return True
    except Exception as e:
        add_message("assistant", f"❌ Error loading file: {str(e)}")
        return False


# ============================================================================
# PROCESS USER ACTIONS
# ============================================================================
def process_action(action: str):
    """Process user action and generate response."""
    df = st.session_state.df
    summary = st.session_state.summary
    
    # Data loading actions
    if action == "upload":
        st.session_state.show_upload = True
        return
    
    if action.startswith("sample_"):
        sample_map = {
            "sample_fitness": "data/samples/fitness_tracker.csv",
            "sample_airbnb": "data/samples/nyc_airbnb.csv", 
            "sample_ecommerce": "data/samples/ecommerce_sales.csv",
        }
        path = sample_map.get(action)
        if path and Path(path).exists():
            add_message("user", f"Load {path.split('/')[-1].replace('.csv', '').replace('_', ' ').title()} sample")
            if load_data(path):
                msg = get_data_loaded_message(st.session_state.summary, st.session_state.filename)
                opts = get_exploration_options(st.session_state.summary)
                add_message("assistant", msg, opts)
        return
    
    if action == "new_data":
        st.session_state.state = ConversationState.DATA_SELECTION
        add_message("assistant", "**Choose your data source:**", get_data_options())
        return
    
    if action == "back":
        opts = get_exploration_options(summary)
        add_message("assistant", "**What would you like to explore?**", opts)
        return
    
    # Analysis actions
    if action == "stats":
        add_message("user", "Show statistics summary")
        result = get_statistics(df)
        opts = get_after_action_options(summary)
        add_message("assistant", result + get_after_action_message(), opts)
        return
    
    if action == "missing":
        add_message("user", "Check for missing values")
        result = get_missing_values(df)
        opts = get_after_action_options(summary)
        add_message("assistant", result + get_after_action_message(), opts)
        return
    
    if action == "heatmap":
        add_message("user", "Show correlation heatmap")
        text, fig = create_heatmap(df)
        opts = get_after_action_options(summary)
        add_message("assistant", text + get_after_action_message(), opts, fig)
        return
    
    if action.startswith("histogram_"):
        col = action.replace("histogram_", "")
        add_message("user", f"Show histogram of {col}")
        text, fig = create_histogram(df, col)
        opts = get_after_action_options(summary)
        add_message("assistant", text + get_after_action_message(), opts, fig)
        return
    
    if action.startswith("bar_"):
        col = action.replace("bar_", "")
        add_message("user", f"Show bar chart of {col}")
        text, fig = create_bar_chart(df, col)
        opts = get_after_action_options(summary)
        add_message("assistant", text + get_after_action_message(), opts, fig)
        return
    
    if action.startswith("scatter_"):
        parts = action.replace("scatter_", "").split("_")
        if len(parts) >= 2:
            x, y = parts[0], parts[1]
            add_message("user", f"Show scatter plot of {x} vs {y}")
            text, fig = create_scatter(df, x, y)
            opts = get_after_action_options(summary)
            add_message("assistant", text + get_after_action_message(), opts, fig)
        return
    
    if action.startswith("outliers_"):
        col = action.replace("outliers_", "")
        if col == "menu":
            opts = [{"label": f"🎯 {c}", "action": f"outliers_{c}"} for c in summary['numeric_columns'][:6]]
            opts.append({"label": "⬅️ Back", "action": "back"})
            add_message("assistant", "**Which column to check for outliers?**", opts)
        else:
            add_message("user", f"Find outliers in {col}")
            text, fig = get_outliers(df, col)
            opts = get_after_action_options(summary)
            add_message("assistant", text + get_after_action_message(), opts, fig)
        return
    
    if action == "viz_menu":
        opts = get_visualization_options(summary)
        add_message("assistant", "**Choose a visualization:**", opts)
        return
    
    if action == "predict_start":
        opts = get_prediction_options(summary)
        add_message("assistant", "**What would you like to predict?**\n\nI'll build a machine learning model to predict your chosen target.", opts)
        return
    
    if action.startswith("predict_"):
        target = action.replace("predict_", "")
        add_message("user", f"Predict {target}")
        text, fig = train_prediction_model(df, target)
        opts = get_after_action_options(summary)
        add_message("assistant", text + get_after_action_message(), opts, fig)
        return
    
    if action == "free_input":
        add_message("assistant", "**Type your question below!**\n\nYou can ask things like:\n• 'Show histogram of price'\n• 'What's the correlation between X and Y?'\n• 'Find outliers in column_name'\n• 'Predict target_column'")
        return


def process_free_text(text: str):
    """Process free text input."""
    df = st.session_state.df
    summary = st.session_state.summary
    
    if df is None:
        add_message("assistant", "Please load some data first!", get_data_options())
        return
    
    text_lower = text.lower()
    
    # Find mentioned columns
    mentioned_numeric = [c for c in summary['numeric_columns'] if c.lower() in text_lower]
    mentioned_cat = [c for c in summary['categorical_columns'] if c.lower() in text_lower]
    
    # Statistics
    if any(w in text_lower for w in ["statistic", "stats", "describe", "summary"]):
        col = mentioned_numeric[0] if mentioned_numeric else None
        result = get_statistics(df, col)
        add_message("assistant", result + get_after_action_message(), get_after_action_options(summary))
        return
    
    # Missing values
    if any(w in text_lower for w in ["missing", "null", "nan", "empty"]):
        result = get_missing_values(df)
        add_message("assistant", result + get_after_action_message(), get_after_action_options(summary))
        return
    
    # Heatmap / correlation
    if any(w in text_lower for w in ["heatmap", "correlation matrix", "correlations"]):
        text_result, fig = create_heatmap(df)
        add_message("assistant", text_result + get_after_action_message(), get_after_action_options(summary), fig)
        return
    
    # Histogram
    if any(w in text_lower for w in ["histogram", "distribution", "dist"]):
        col = mentioned_numeric[0] if mentioned_numeric else (summary['numeric_columns'][0] if summary['numeric_columns'] else None)
        if col:
            text_result, fig = create_histogram(df, col)
            add_message("assistant", text_result + get_after_action_message(), get_after_action_options(summary), fig)
        else:
            add_message("assistant", "No numeric column found. Please specify a column name.")
        return
    
    # Scatter
    if any(w in text_lower for w in ["scatter", "relationship", "vs"]):
        if len(mentioned_numeric) >= 2:
            x, y = mentioned_numeric[0], mentioned_numeric[1]
        elif len(summary['numeric_columns']) >= 2:
            x, y = summary['numeric_columns'][0], summary['numeric_columns'][1]
        else:
            add_message("assistant", "Need at least 2 numeric columns for scatter plot.")
            return
        text_result, fig = create_scatter(df, x, y)
        add_message("assistant", text_result + get_after_action_message(), get_after_action_options(summary), fig)
        return
    
    # Bar chart
    if any(w in text_lower for w in ["bar", "count", "frequency"]):
        col = mentioned_cat[0] if mentioned_cat else (mentioned_numeric[0] if mentioned_numeric else None)
        if not col and summary['categorical_columns']:
            col = summary['categorical_columns'][0]
        if col:
            text_result, fig = create_bar_chart(df, col)
            add_message("assistant", text_result + get_after_action_message(), get_after_action_options(summary), fig)
        else:
            add_message("assistant", "Please specify a column for the bar chart.")
        return
    
    # Outliers
    if "outlier" in text_lower:
        col = mentioned_numeric[0] if mentioned_numeric else (summary['numeric_columns'][0] if summary['numeric_columns'] else None)
        if col:
            text_result, fig = get_outliers(df, col)
            add_message("assistant", text_result + get_after_action_message(), get_after_action_options(summary), fig)
        else:
            add_message("assistant", "Please specify a numeric column to check for outliers.")
        return
    
    # Prediction
    if any(w in text_lower for w in ["predict", "forecast", "model"]):
        target = mentioned_numeric[0] if mentioned_numeric else (summary['numeric_columns'][-1] if summary['numeric_columns'] else None)
        if target:
            text_result, fig = train_prediction_model(df, target)
            add_message("assistant", text_result + get_after_action_message(), get_after_action_options(summary), fig)
        else:
            add_message("assistant", "Please specify a numeric column to predict.")
        return
    
    # Pie chart
    if "pie" in text_lower:
        col = mentioned_cat[0] if mentioned_cat else (summary['categorical_columns'][0] if summary['categorical_columns'] else None)
        if col:
            text_result, fig = create_pie_chart(df, col)
            add_message("assistant", text_result + get_after_action_message(), get_after_action_options(summary), fig)
        else:
            add_message("assistant", "Please specify a categorical column for pie chart.")
        return
    
    # Column list
    if any(w in text_lower for w in ["column", "columns", "schema", "fields"]):
        cols_text = "**Your columns:**\n\n"
        cols_text += "**Numeric:** " + ", ".join(summary['numeric_columns']) + "\n\n"
        cols_text += "**Categorical:** " + ", ".join(summary['categorical_columns'])
        add_message("assistant", cols_text + get_after_action_message(), get_after_action_options(summary))
        return
    
    # Default: show options
    add_message("assistant", "I'm not sure what you mean. Here are some things I can do:" + get_after_action_message(), 
                get_exploration_options(summary))


# ============================================================================
# RENDER CHAT
# ============================================================================
def render_chat():
    """Render the chat interface."""
    
    # Display all messages
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f"""<div class="user-msg">{msg["content"]}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="bot-msg">{msg["content"]}</div>""", unsafe_allow_html=True)
            
            # Show figure if present
            if msg.get("figure"):
                st.plotly_chart(msg["figure"], use_container_width=True, key=f"fig_{i}")
            
            # Show option buttons if present
            if msg.get("options") and i == len(st.session_state.messages) - 1:
                cols = st.columns(min(len(msg["options"]), 3))
                for j, opt in enumerate(msg["options"]):
                    col_idx = j % 3
                    with cols[col_idx]:
                        if st.button(opt["label"], key=f"opt_{i}_{j}", use_container_width=True):
                            add_message("user", opt["label"])
                            process_action(opt["action"])
                            st.rerun()
    
    # Scroll anchor
    st.markdown('<div class="scroll-anchor"></div>', unsafe_allow_html=True)


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    init_session()
    
    # Minimal sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # LLM toggle
        llm_available = st.session_state.llm_client is not None
        if llm_available:
            st.session_state.use_llm = st.toggle("🧠 Use AI (LLM)", value=st.session_state.use_llm,
                                                   help="Enable natural language understanding")
            if st.session_state.use_llm:
                st.success("AI mode: ON")
            else:
                st.info("Offline mode: ON")
        else:
            st.info("💡 Add GROQ_API_KEY to .env for AI mode")
        
        st.divider()
        
        # Data info
        if st.session_state.df is not None:
            st.markdown(f"**📊 Current data:**")
            st.markdown(f"{st.session_state.filename}")
            st.caption(f"{st.session_state.summary['rows']} rows × {st.session_state.summary['columns']} cols")
            
            if st.button("📂 Load new data", use_container_width=True):
                add_message("assistant", "**Choose your data source:**", get_data_options())
                st.rerun()
        
        st.divider()
        
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.state = ConversationState.WELCOME
            st.rerun()
    
    # Main chat area
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Initialize with welcome message
    if not st.session_state.messages:
        add_message("assistant", get_welcome_message(), get_data_options())
    
    # File upload area (shown when requested)
    if st.session_state.show_upload:
        uploaded = st.file_uploader("Upload your CSV file:", type=["csv"], key="uploader")
        if uploaded:
            st.session_state.show_upload = False
            add_message("user", f"Upload {uploaded.name}")
            if load_data(uploaded, uploaded.name):
                msg = get_data_loaded_message(st.session_state.summary, st.session_state.filename)
                opts = get_exploration_options(st.session_state.summary)
                add_message("assistant", msg, opts)
            st.rerun()
    
    # Render chat
    render_chat()
    
    # Text input at bottom
    user_input = st.chat_input("Type your question or click an option above...")
    if user_input:
        add_message("user", user_input)
        process_free_text(user_input)
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-scroll JavaScript
    st.markdown("""
    <script>
        window.scrollTo(0, document.body.scrollHeight);
    </script>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
