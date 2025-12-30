"""
🤖 OmniAgent v2 - AI Data Analysis Assistant
=============================================
Works WITH or WITHOUT Groq API key!
Reads GROQ_API_KEY and LLM_MODEL from .env file

Run: streamlit run app_with_llm.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
import json
import re
import os
from typing import Optional, Tuple, List, Dict, Any

# Load .env file
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
    initial_sidebar_state="expanded"
)

st.markdown("""<style>
.info-box { background-color: #e8f4f8; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f77b4; margin: 1rem 0; }
</style>""", unsafe_allow_html=True)

# ============================================================================
# GROQ CLIENT
# ============================================================================
class GroqClient:
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.last_error = None
    
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
                self.last_error = "rate_limit"
                return None
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            self.last_error = str(e)
            return None

# ============================================================================
# AGENTS
# ============================================================================
class SchemaAgent:
    @staticmethod
    def get_schema(df: pd.DataFrame) -> Dict:
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "all_columns": df.columns.tolist(),
        }
    
    @staticmethod
    def get_sample(df: pd.DataFrame, n: int = 5) -> str:
        return df.head(n).to_string()

class StatsAgent:
    @staticmethod
    def describe(df: pd.DataFrame, column: str = None) -> Dict:
        if column and column in df.columns:
            return {column: df[column].describe().to_dict()}
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {"error": "No numeric columns"}
        return {col: numeric_df[col].describe().to_dict() for col in numeric_df.columns}
    
    @staticmethod
    def correlation(df: pd.DataFrame) -> Dict:
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return {"error": "Need 2+ numeric columns"}
        return numeric_df.corr().round(4).to_dict()
    
    @staticmethod
    def outliers(df: pd.DataFrame, column: str) -> Dict:
        if column not in df.columns:
            return {"error": f"Column '{column}' not found"}
        data = df[column].dropna()
        if not np.issubdtype(data.dtype, np.number):
            return {"error": f"Column '{column}' is not numeric"}
        Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
        IQR = Q3 - Q1
        lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        outliers = data[(data < lower) | (data > upper)]
        return {
            "column": column, "outlier_count": len(outliers),
            "outlier_percentage": round(len(outliers) / len(data) * 100, 2),
            "lower_bound": round(float(lower), 4), "upper_bound": round(float(upper), 4),
            "sample_outliers": outliers.head(5).tolist()
        }
    
    @staticmethod
    def missing_values(df: pd.DataFrame) -> Dict:
        missing = df.isnull().sum()
        return {col: {"count": int(missing[col]), "percent": round(missing[col] / len(df) * 100, 2)} for col in df.columns}

class PlotAgent:
    @staticmethod
    def histogram(df: pd.DataFrame, column: str = None) -> Tuple[Any, str]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not column:
            column = numeric_cols[0] if numeric_cols else None
        if not column or column not in df.columns:
            return None, "No valid column"
        fig = px.histogram(df, x=column, title=f"📊 Distribution of {column}", template="plotly_white", color_discrete_sequence=["#667eea"])
        return fig, None
    
    @staticmethod
    def scatter(df: pd.DataFrame, x: str = None, y: str = None) -> Tuple[Any, str]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) < 2:
            return None, "Need 2+ numeric columns"
        x = x or numeric_cols[0]
        y = y or numeric_cols[1]
        fig = px.scatter(df, x=x, y=y, title=f"📈 {x} vs {y}", template="plotly_white", trendline="ols")
        return fig, None
    
    @staticmethod
    def bar(df: pd.DataFrame, column: str = None) -> Tuple[Any, str]:
        all_cols = df.columns.tolist()
        column = column or all_cols[0]
        if column not in df.columns:
            return None, f"Column '{column}' not found"
        counts = df[column].value_counts().head(15)
        fig = px.bar(x=counts.index, y=counts.values, title=f"📊 Count by {column}", template="plotly_white", color_discrete_sequence=["#764ba2"])
        return fig, None
    
    @staticmethod
    def box(df: pd.DataFrame, column: str = None) -> Tuple[Any, str]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        column = column or (numeric_cols[0] if numeric_cols else None)
        if not column:
            return None, "No numeric columns"
        fig = px.box(df, y=column, title=f"📦 Box Plot of {column}", template="plotly_white")
        return fig, None
    
    @staticmethod
    def heatmap(df: pd.DataFrame) -> Tuple[Any, str]:
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return None, "Need 2+ numeric columns"
        corr = numeric_df.corr()
        fig = px.imshow(corr, title="🔥 Correlation Heatmap", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, text_auto=".2f", template="plotly_white")
        return fig, None
    
    @staticmethod
    def pie(df: pd.DataFrame, column: str = None) -> Tuple[Any, str]:
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        column = column or (cat_cols[0] if cat_cols else None)
        if not column:
            return None, "No categorical columns"
        counts = df[column].value_counts().head(10)
        fig = px.pie(values=counts.values, names=counts.index, title=f"🥧 {column}", template="plotly_white")
        return fig, None

class PredictionAgent:
    @staticmethod
    def train_model(df: pd.DataFrame, target: str, features: List[str] = None, model_type: str = "random_forest") -> Dict:
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LinearRegression
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
        
        if target not in df.columns:
            return {"error": f"Target '{target}' not found"}
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if target not in numeric_cols:
            return {"error": f"Target '{target}' must be numeric"}
        
        features = features or [c for c in numeric_cols if c != target]
        features = [f for f in features if f in numeric_cols and f != target]
        if not features:
            return {"error": "No valid features"}
        
        X = df[features].dropna()
        y = df.loc[X.index, target].dropna()
        X = X.loc[y.index]
        
        if len(X) < 20:
            return {"error": "Need at least 20 rows"}
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        models = {"linear": LinearRegression(), "gradient_boosting": GradientBoostingRegressor(n_estimators=100, random_state=42)}
        model = models.get(model_type, RandomForestRegressor(n_estimators=100, random_state=42))
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        result = {
            "model": model_type, "target": target, "features": features,
            "metrics": {"R²": round(r2_score(y_test, y_pred), 4), "RMSE": round(np.sqrt(mean_squared_error(y_test, y_pred)), 4), "MAE": round(mean_absolute_error(y_test, y_pred), 4)}
        }
        if hasattr(model, 'feature_importances_'):
            result["feature_importance"] = dict(sorted(zip(features, model.feature_importances_.round(4)), key=lambda x: -x[1]))
        return result

# ============================================================================
# MASTER AGENT
# ============================================================================
class MasterAgent:
    def __init__(self, df: pd.DataFrame = None, llm: GroqClient = None):
        self.df = df
        self.llm = llm
        self.schema = SchemaAgent.get_schema(df) if df is not None else None
        self.history = []
    
    def chat(self, message: str) -> Tuple[str, Any]:
        if self.df is None:
            return "⚠️ Please load a dataset first!", None
        
        # Try LLM first
        if self.llm:
            result = self._llm_chat(message)
            if result:
                return result
        
        # Fallback to keywords
        return self._keyword_chat(message)
    
    def _llm_chat(self, message: str) -> Optional[Tuple[str, Any]]:
        prompt = f"""Dataset: {self.schema['total_rows']} rows, {self.schema['total_columns']} cols
Columns: {', '.join(self.schema['all_columns'][:15])}
Numeric: {', '.join(self.schema['numeric_columns'][:10])}

Return ONLY JSON:
{{"action": "stats", "type": "describe"}}
{{"action": "stats", "type": "outliers", "params": {{"column": "COL"}}}}
{{"action": "stats", "type": "missing"}}
{{"action": "plot", "type": "histogram", "params": {{"column": "COL"}}}}
{{"action": "plot", "type": "heatmap"}}
{{"action": "plot", "type": "bar", "params": {{"column": "COL"}}}}
{{"action": "predict", "params": {{"target": "COL"}}}}"""
        
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": message}]
        response = self.llm.chat(messages)
        
        if not response:
            return None
        
        try:
            match = re.search(r'\{[^{}]*\}', response)
            if match:
                cmd = json.loads(match.group())
                return self._execute(cmd)
        except:
            pass
        return None
    
    def _execute(self, cmd: Dict) -> Tuple[str, Any]:
        action = cmd.get("action")
        params = cmd.get("params", {})
        
        if action == "stats":
            stat_type = cmd.get("type", "describe")
            if stat_type == "describe":
                result = StatsAgent.describe(self.df, params.get("column"))
            elif stat_type == "outliers":
                col = params.get("column") or self.schema['numeric_columns'][0]
                result = StatsAgent.outliers(self.df, col)
            elif stat_type == "missing":
                result = StatsAgent.missing_values(self.df)
            else:
                result = StatsAgent.describe(self.df)
            return f"```json\n{json.dumps(result, indent=2, default=str)}\n```", None
        
        elif action == "plot":
            plot_type = cmd.get("type", "histogram")
            col = params.get("column")
            if plot_type == "histogram":
                fig, err = PlotAgent.histogram(self.df, col)
            elif plot_type == "scatter":
                fig, err = PlotAgent.scatter(self.df, params.get("x"), params.get("y"))
            elif plot_type == "bar":
                fig, err = PlotAgent.bar(self.df, col)
            elif plot_type == "box":
                fig, err = PlotAgent.box(self.df, col)
            elif plot_type == "heatmap":
                fig, err = PlotAgent.heatmap(self.df)
            elif plot_type == "pie":
                fig, err = PlotAgent.pie(self.df, col)
            else:
                return f"Unknown plot: {plot_type}", None
            if err:
                return f"⚠️ {err}", None
            return "✅ Chart created!", fig
        
        elif action == "predict":
            result = PredictionAgent.train_model(self.df, params.get("target"), params.get("features"))
            return f"```json\n{json.dumps(result, indent=2)}\n```", None
        
        return "Processed", None
    
    def _keyword_chat(self, msg: str) -> Tuple[str, Any]:
        msg = msg.lower()
        num_cols = self.schema['numeric_columns']
        cat_cols = self.schema['categorical_columns']
        
        # Find mentioned columns
        mentioned_num = [c for c in num_cols if c.lower() in msg]
        mentioned_cat = [c for c in cat_cols if c.lower() in msg]
        
        # Statistics
        if any(w in msg for w in ["describe", "statistic", "stats", "summary"]):
            col = mentioned_num[0] if mentioned_num else None
            result = StatsAgent.describe(self.df, col)
            return f"📊 **Statistics:**\n```json\n{json.dumps(result, indent=2, default=str)}\n```", None
        
        if any(w in msg for w in ["missing", "null", "nan"]):
            result = StatsAgent.missing_values(self.df)
            return f"🔍 **Missing Values:**\n```json\n{json.dumps(result, indent=2)}\n```", None
        
        if "outlier" in msg:
            col = mentioned_num[0] if mentioned_num else (num_cols[0] if num_cols else None)
            if col:
                result = StatsAgent.outliers(self.df, col)
                return f"🔎 **Outliers in {col}:**\n```json\n{json.dumps(result, indent=2)}\n```", None
            return "⚠️ No numeric column for outliers", None
        
        # Visualizations
        if any(w in msg for w in ["heatmap", "correlation matrix"]):
            fig, err = PlotAgent.heatmap(self.df)
            if err:
                result = StatsAgent.correlation(self.df)
                return f"📊 **Correlation:**\n```json\n{json.dumps(result, indent=2)}\n```", None
            return "🔥 **Correlation Heatmap:**", fig
        
        if "correlation" in msg:
            result = StatsAgent.correlation(self.df)
            return f"📊 **Correlation:**\n```json\n{json.dumps(result, indent=2)}\n```", None
        
        if any(w in msg for w in ["histogram", "distribution", "dist"]):
            col = mentioned_num[0] if mentioned_num else (num_cols[0] if num_cols else None)
            if col:
                fig, err = PlotAgent.histogram(self.df, col)
                if err:
                    return f"⚠️ {err}", None
                return f"📊 **Distribution of {col}:**", fig
            return "⚠️ No numeric column", None
        
        if any(w in msg for w in ["scatter", "vs", "relationship"]):
            if len(num_cols) >= 2:
                x = mentioned_num[0] if mentioned_num else num_cols[0]
                y = mentioned_num[1] if len(mentioned_num) > 1 else num_cols[1]
                fig, _ = PlotAgent.scatter(self.df, x, y)
                return f"📈 **{x} vs {y}:**", fig
            return "⚠️ Need 2 numeric columns", None
        
        if any(w in msg for w in ["bar", "count", "frequency"]):
            col = mentioned_cat[0] if mentioned_cat else (cat_cols[0] if cat_cols else None)
            if col:
                fig, _ = PlotAgent.bar(self.df, col)
                return f"📊 **Bar Chart of {col}:**", fig
            return "⚠️ No categorical column", None
        
        if any(w in msg for w in ["box", "boxplot"]):
            col = mentioned_num[0] if mentioned_num else (num_cols[0] if num_cols else None)
            if col:
                fig, _ = PlotAgent.box(self.df, col)
                return f"📦 **Box Plot of {col}:**", fig
            return "⚠️ No numeric column", None
        
        if any(w in msg for w in ["pie", "proportion"]):
            col = mentioned_cat[0] if mentioned_cat else (cat_cols[0] if cat_cols else None)
            if col:
                fig, _ = PlotAgent.pie(self.df, col)
                return f"🥧 **Pie Chart of {col}:**", fig
            return "⚠️ No categorical column", None
        
        # Prediction
        if any(w in msg for w in ["predict", "model", "train", "forecast"]):
            target = mentioned_num[0] if mentioned_num else (num_cols[-1] if num_cols else None)
            if target:
                features = [c for c in num_cols if c != target][:5]
                result = PredictionAgent.train_model(self.df, target, features)
                return f"🤖 **Model for {target}:**\n```json\n{json.dumps(result, indent=2)}\n```", None
            return "⚠️ No target column", None
        
        # Schema/sample
        if any(w in msg for w in ["schema", "columns", "info"]):
            return f"📋 **Schema:**\n```json\n{json.dumps(self.schema, indent=2)}\n```", None
        
        if any(w in msg for w in ["sample", "head", "preview", "show data"]):
            return SchemaAgent.get_sample(self.df, 5), None
        
        # Help
        return self._help(), None
    
    def _help(self) -> str:
        return f"""🤔 **Try these:**

📊 **Statistics:** "Show statistics", "Find missing values", "Find outliers in {self.schema['numeric_columns'][0] if self.schema['numeric_columns'] else 'column'}"

📈 **Charts:** "Show histogram of {self.schema['numeric_columns'][0] if self.schema['numeric_columns'] else 'column'}", "Correlation heatmap", "Bar chart", "Scatter plot"

🔮 **Predict:** "Predict {self.schema['numeric_columns'][-1] if self.schema['numeric_columns'] else 'target'}"

**Your columns:** {', '.join(self.schema['all_columns'][:8])}"""

# ============================================================================
# STREAMLIT UI
# ============================================================================
def init_state():
    for k, v in {"df": None, "filename": None, "agent": None, "history": [], "api_key": None}.items():
        if k not in st.session_state:
            st.session_state[k] = v

def load_data(source, filename=None):
    try:
        df = pd.read_csv(source)
        st.session_state.df = df
        st.session_state.filename = filename or (Path(source).name if isinstance(source, (str, Path)) else "data.csv")
        
        api_key = st.session_state.api_key or os.getenv("GROQ_API_KEY")
        llm = GroqClient(api_key) if api_key else None
        st.session_state.agent = MasterAgent(df, llm)
        st.session_state.history = []
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def sidebar():
    with st.sidebar:
        st.markdown("## 🤖 OmniAgent")
        st.divider()
        
        # API Key
        env_key = os.getenv("GROQ_API_KEY")
        st.markdown("### 🔑 API Key")
        if env_key:
            st.success("✅ Loaded from .env")
            st.session_state.api_key = env_key
            model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
            st.info(f"Model: {model}")
        else:
            key = st.text_input("Groq API Key:", type="password")
            if key:
                st.session_state.api_key = key
                st.success("✅ Key set")
            else:
                st.warning("No key - using keywords (works!)")
        
        st.divider()
        
        # Data
        st.markdown("### 📁 Load Data")
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded and st.session_state.filename != uploaded.name:
            if load_data(uploaded, uploaded.name):
                st.rerun()
        
        st.markdown("**Samples:**")
        samples = Path("data/samples")
        if samples.exists():
            for f in samples.glob("*.csv"):
                if st.button(f"📊 {f.stem}", key=f.name, use_container_width=True):
                    if load_data(f):
                        st.rerun()
        
        if st.session_state.df is not None:
            st.divider()
            st.markdown(f"### 📋 {st.session_state.filename}")
            st.caption(f"Rows: {len(st.session_state.df)} | Cols: {len(st.session_state.df.columns)}")
            if st.button("🗑️ Clear Chat"):
                st.session_state.history = []
                st.rerun()

def main_area():
    if st.session_state.df is None:
        st.markdown("# 🤖 Welcome to OmniAgent!")
        st.markdown("Load a dataset from the sidebar to start analyzing.")
        st.markdown("""
| Agent | Purpose |
|-------|---------|
| 📋 Schema | Data structure |
| 📊 Stats | Statistics & outliers |
| 📈 Plot | Visualizations |
| 🔮 Predict | ML models |
        """)
        st.info("💡 Works with or without API key!")
        return
    
    df = st.session_state.df
    agent = st.session_state.agent
    
    st.markdown(f"### 💬 Chat: {st.session_state.filename}")
    
    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", len(df))
    c2.metric("Columns", len(df.columns))
    c3.metric("Numeric", len(agent.schema['numeric_columns']))
    c4.metric("Categorical", len(agent.schema['categorical_columns']))
    
    # Quick actions
    st.markdown("#### ⚡ Quick Actions")
    cols = st.columns(6)
    actions = [
        ("📊 Stats", "Show descriptive statistics"),
        ("🔍 Missing", "Check missing values"),
        ("🔥 Heatmap", "Show correlation heatmap"),
        ("📈 Histogram", f"Histogram of {agent.schema['numeric_columns'][0]}" if agent.schema['numeric_columns'] else "Histogram"),
        ("🎯 Outliers", f"Find outliers in {agent.schema['numeric_columns'][0]}" if agent.schema['numeric_columns'] else "Outliers"),
        ("📋 Sample", "Show sample data"),
    ]
    for i, (label, query) in enumerate(actions):
        with cols[i]:
            if st.button(label, key=f"act_{i}", use_container_width=True):
                st.session_state.history.append({"role": "user", "content": query})
                resp, fig = agent.chat(query)
                st.session_state.history.append({"role": "assistant", "content": resp, "fig": fig})
                st.rerun()
    
    st.divider()
    
    # Chat history
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.markdown(f"**👤 You:** {msg['content']}")
        else:
            st.markdown(f"**🤖 OmniAgent:**")
            st.markdown(msg["content"])
            if msg.get("fig"):
                st.plotly_chart(msg["fig"], use_container_width=True)
    
    # Input
    user_input = st.chat_input("Ask about your data...")
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        resp, fig = agent.chat(user_input)
        st.session_state.history.append({"role": "assistant", "content": resp, "fig": fig})
        st.rerun()

def main():
    init_state()
    sidebar()
    main_area()

if __name__ == "__main__":
    main()
