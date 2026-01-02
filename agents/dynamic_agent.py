"""
Dynamic Agent Module
====================
Handles requests that go beyond built-in agent capabilities
by dynamically generating and executing code via LLM.

THREE-STEP FLOW (Resource Optimized):
1. OFFER: "I don't have this built-in, but I can create it. Want me to?" → yes/no
2. PLAN: Generate code, show plan → "Ready to execute?" → yes/no  
3. EXECUTE: Run code, show results

This saves LLM API calls if user declines at step 1.

Made with ❤️ by Hooman Esteki
https://esteki.ca/
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, Any, Optional
import traceback
import re

# Safe imports for code execution
SAFE_MODULES = {
    'pd': pd,
    'np': np,
    'pandas': pd,
    'numpy': np,
}

# Try to import plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
    SAFE_MODULES['px'] = px
    SAFE_MODULES['go'] = go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Try to import sklearn
try:
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class DynamicAgent:
    """
    Dynamic Agent - Creates custom analysis on-the-fly using LLM.
    
    Three-step confirmation flow:
    1. Offer to create custom analysis
    2. Show plan and code for approval
    3. Execute on confirmation
    """
    
    name = "Dynamic Agent"
    emoji = "🔮"
    description = "Creates custom analysis dynamically"
    
    # States for the flow
    STATE_IDLE = 'idle'
    STATE_OFFERED = 'offered'      # Step 1: Offered to create, waiting for yes/no
    STATE_PLANNED = 'planned'      # Step 2: Plan shown, waiting for yes/no
    
    # Dangerous patterns to block in CODE
    BLOCKED_CODE_PATTERNS = [
        r'import\s+os\b',
        r'import\s+sys\b',
        r'import\s+subprocess',
        r'import\s+shutil',
        r'from\s+os\s+import',
        r'from\s+sys\s+import',
        r'from\s+subprocess\s+import',
        r'__import__',
        r'eval\s*\(',
        r'exec\s*\(',
        r'compile\s*\(',
        r'open\s*\(',
        r'file\s*\(',
        r'input\s*\(',
        r'raw_input',
        r'\bos\.',
        r'\bsys\.',
        r'subprocess\.',
        r'shutil\.',
        r'\.write\s*\(',
        r'\.read\s*\(',
        r'requests\.',
        r'urllib',
        r'\bsocket\b',
        r'\bpickle\b',
        r'\bmarshal\b',
        r'globals\s*\(',
        r'locals\s*\(',
        r'getattr\s*\(',
        r'setattr\s*\(',
        r'delattr\s*\(',
        r'__builtins__',
        r'__class__',
        r'__bases__',
        r'__subclasses__',
        r'__code__',
        r'__globals__',
        r'breakpoint\s*\(',
        r'pdb\.',
        r'debugger',
    ]
    
    # Confirmation words (expanded)
    YES_WORDS = ['yes', 'y', 'ok', 'go', 'proceed', 'execute', 'run', 'do it', 
                 'confirm', 'sure', 'yep', 'yeah', 'run it', 'create', 'build',
                 'make it', 'go ahead', 'please', 'continue', 'let\'s do it']
    NO_WORDS = ['no', 'n', 'cancel', 'stop', 'nevermind', 'never mind', 'abort', 
                'nope', 'dont', "don't", 'skip', 'forget it', 'not now']
    
    # Categories of dynamic analysis for better descriptions
    ANALYSIS_CATEGORIES = {
        'rolling': {
            'name': 'Rolling/Moving Average',
            'description': 'Calculate averages over a sliding window of data points',
            'example': 'rolling 7-day average, moving average'
        },
        'outlier': {
            'name': 'Outlier Detection',
            'description': 'Find unusual values using statistical methods (IQR, Z-score)',
            'example': 'find outliers, detect anomalies'
        },
        'regression': {
            'name': 'Regression Analysis',
            'description': 'Add trend/regression lines to visualize relationships',
            'example': 'scatter with regression line, trend analysis'
        },
        'binning': {
            'name': 'Data Binning/Categorization',
            'description': 'Create categories from continuous data',
            'example': 'bin age into groups, categorize values'
        },
        'ranking': {
            'name': 'Ranking/Top N',
            'description': 'Find top or bottom records by some criteria',
            'example': 'top 10 by ratio, rank by value'
        },
        'zscore': {
            'name': 'Standardization/Z-Scores',
            'description': 'Normalize data using statistical transformations',
            'example': 'calculate z-scores, standardize column'
        },
        'correlation': {
            'name': 'Advanced Correlation',
            'description': 'Partial correlations or correlation with controls',
            'example': 'correlation controlling for X'
        },
        'custom': {
            'name': 'Custom Analysis',
            'description': 'Custom Python code for your specific analysis need',
            'example': 'various custom calculations'
        }
    }
    
    def __init__(self, analyzer=None, llm=None):
        self.analyzer = analyzer
        self.llm = llm
    
    def can_handle(self, query: str) -> bool:
        """Check if this agent should handle the query."""
        return True
    
    def _init_state(self):
        """Initialize session state for dynamic agent."""
        if 'dynamic_state' not in st.session_state:
            st.session_state.dynamic_state = self.STATE_IDLE
        if 'dynamic_query' not in st.session_state:
            st.session_state.dynamic_query = None
        if 'dynamic_plan' not in st.session_state:
            st.session_state.dynamic_plan = None
        if 'dynamic_code' not in st.session_state:
            st.session_state.dynamic_code = None
        if 'dynamic_category' not in st.session_state:
            st.session_state.dynamic_category = None
    
    def _reset_state(self):
        """Reset the dynamic agent state."""
        st.session_state.dynamic_state = self.STATE_IDLE
        st.session_state.dynamic_query = None
        st.session_state.dynamic_plan = None
        st.session_state.dynamic_code = None
        st.session_state.dynamic_category = None
    
    def _get_df_info(self) -> Dict[str, Any]:
        """Get information about the dataframe for LLM context."""
        if self.analyzer is None or self.analyzer.df is None:
            return {}
        
        df = self.analyzer.df
        
        return {
            'shape': df.shape,
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'numeric_cols': list(df.select_dtypes(include=[np.number]).columns),
            'categorical_cols': list(df.select_dtypes(include=['object', 'category']).columns),
            'sample': df.head(3).to_string(),
            'columns': list(df.columns),
        }
    
    def _detect_category(self, query: str) -> str:
        """Detect what category of analysis the user wants."""
        q = query.lower()
        
        if any(w in q for w in ['rolling', 'moving', 'window', 'sliding', '7-day', '5-day', '30-day']):
            return 'rolling'
        elif any(w in q for w in ['outlier', 'anomaly', 'iqr', 'unusual', 'extreme']):
            return 'outlier'
        elif any(w in q for w in ['regression', 'trend', 'trendline', 'best fit', 'linear fit']):
            return 'regression'
        elif any(w in q for w in ['bin', 'bucket', 'categorize', 'category', 'group into', 'split into']):
            return 'binning'
        elif any(w in q for w in ['top', 'bottom', 'rank', 'highest', 'lowest', 'ratio']):
            return 'ranking'
        elif any(w in q for w in ['z-score', 'zscore', 'standardize', 'normalize']):
            return 'zscore'
        elif any(w in q for w in ['partial', 'controlling', 'control for']):
            return 'correlation'
        else:
            return 'custom'
    
    def _is_code_safe(self, code: str) -> tuple[bool, str]:
        """Check if generated code is safe to execute."""
        for pattern in self.BLOCKED_CODE_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Blocked pattern detected: {pattern}"
        
        if len(code) > 5000:
            return False, "Code too long"
        
        return True, "OK"
    
    def _is_confirmation(self, query: str) -> Optional[bool]:
        """
        Check if query is a confirmation response.
        Returns: True for yes, False for no, None if not a confirmation
        """
        q = query.lower().strip()
        
        # Remove emojis and special chars for matching
        q_clean = re.sub(r'[^\w\s]', '', q).strip().lower()
        
        # Very short responses are likely confirmations
        if len(q_clean) <= 20:
            # Check for yes
            for word in self.YES_WORDS:
                if word in q_clean or q_clean == word:
                    return True
            
            # Check for no
            for word in self.NO_WORDS:
                if word in q_clean or q_clean == word:
                    return False
        
        return None
    
    def _execute_code(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Safely execute generated code."""
        exec_globals = {
            'df': df.copy(),
            'pd': pd,
            'np': np,
            'result': None,
            'result_df': None,
            'fig': None,
        }
        
        if PLOTLY_AVAILABLE:
            exec_globals['px'] = px
            exec_globals['go'] = go
        
        if SKLEARN_AVAILABLE:
            exec_globals['StandardScaler'] = StandardScaler
            exec_globals['LabelEncoder'] = LabelEncoder
            exec_globals['train_test_split'] = train_test_split
            exec_globals['LinearRegression'] = LinearRegression
            exec_globals['LogisticRegression'] = LogisticRegression
            exec_globals['RandomForestClassifier'] = RandomForestClassifier
            exec_globals['RandomForestRegressor'] = RandomForestRegressor
            exec_globals['accuracy_score'] = accuracy_score
            exec_globals['mean_squared_error'] = mean_squared_error
            exec_globals['r2_score'] = r2_score
        
        try:
            exec(code, exec_globals)
            
            return {
                'success': True,
                'result': exec_globals.get('result'),
                'result_df': exec_globals.get('result_df'),
                'fig': exec_globals.get('fig'),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'result': None,
                'result_df': None,
                'fig': None,
                'error': str(e)
            }
    
    def _format_result(self, result: Any) -> str:
        """Safely format result for display."""
        if result is None:
            return "No result returned"
        
        try:
            if isinstance(result, (int, float)):
                return f"**{result:,.4f}**"
            elif isinstance(result, str):
                return result
            elif isinstance(result, dict):
                lines = []
                for k, v in list(result.items())[:20]:
                    if isinstance(v, float):
                        lines.append(f"- **{k}:** {v:,.4f}")
                    else:
                        lines.append(f"- **{k}:** {v}")
                return "\n".join(lines)
            elif isinstance(result, (list, tuple)):
                if len(result) == 0:
                    return "✅ No items found (empty result - this might be expected, e.g., no outliers detected)"
                elif len(result) <= 10:
                    return str(result)
                else:
                    return f"List with {len(result)} items: {result[:5]}... (showing first 5)"
            elif isinstance(result, pd.Series):
                if len(result) <= 10:
                    return result.to_string()
                else:
                    return f"Series with {len(result)} values:\n{result.head(10).to_string()}\n... (showing first 10)"
            elif isinstance(result, pd.DataFrame):
                if len(result) <= 20:
                    return result.to_string()
                else:
                    return f"DataFrame with {len(result)} rows:\n{result.head(10).to_string()}\n... (showing first 10)"
            else:
                return str(result)[:1000]
        except Exception as e:
            return f"Result: {type(result).__name__} (display error: {e})"
    
    def _step1_offer(self, query: str) -> Dict[str, Any]:
        """
        STEP 1: Offer to create custom analysis.
        This is resource-efficient - no LLM call yet.
        """
        category = self._detect_category(query)
        cat_info = self.ANALYSIS_CATEGORIES.get(category, self.ANALYSIS_CATEGORIES['custom'])
        
        # Store state
        st.session_state.dynamic_state = self.STATE_OFFERED
        st.session_state.dynamic_query = query
        st.session_state.dynamic_category = category
        
        # Get column suggestions
        columns_hint = ""
        if self.analyzer and self.analyzer.df is not None:
            num_cols = self.analyzer.usable_numeric[:5]
            cat_cols = self.analyzer.usable_categorical[:3]
            if num_cols:
                columns_hint = f"\n\n**Available numeric columns:** {', '.join(num_cols)}"
            if cat_cols:
                columns_hint += f"\n**Available categorical columns:** {', '.join(cat_cols)}"
        
        content = f"""## 🔮 Custom Analysis Available

**Your request:** "{query}"

---

### 📋 What I'll Create:

| Property | Details |
|----------|---------|
| **Type** | {cat_info['name']} |
| **Description** | {cat_info['description']} |
| **Example** | {cat_info['example']} |
{columns_hint}

---

### ⚡ This requires AI to generate custom code.

**Type `yes` to create the analysis plan** or `no` to cancel.

*I'm asking first because generating the plan uses AI resources.*
"""
        
        return {
            'content': content,
            'insights': "⏳ **Step 1 of 3** - Waiting for confirmation to create analysis plan.",
            'suggestions': ["yes", "no"]
        }
    
    def _step2_plan(self, query: str) -> Dict[str, Any]:
        """
        STEP 2: Generate and show the plan/code.
        This calls the LLM to generate code.
        """
        # Check prerequisites
        if self.llm is None or not self.llm.is_active():
            self._reset_state()
            return {
                'content': """## ⚠️ AI Mode Required

To create custom analysis, I need AI Mode enabled.

### How to Enable:
1. Go to **🧠 AI Assistant** in the sidebar
2. Add your **Groq API Key** (free at console.groq.com)
3. Click **Validate & Save**
4. Try your request again!
""",
                'insights': "Enable AI Mode to use dynamic analysis.",
                'suggestions': self._get_suggestions()
            }
        
        # Get dataframe info
        df_info = self._get_df_info()
        
        # Generate code using LLM
        generated = self.llm.generate_analysis_code(query, df_info)
        
        if not generated or not generated.get('code'):
            self._reset_state()
            return {
                'content': f"""## 🤔 Couldn't Generate Plan

I tried to create a plan for your request, but couldn't generate appropriate code.

**Your question:** "{query}"

### Try:
- Be more specific about which columns to use
- Mention the exact calculation you want
- Break complex questions into simpler parts

**Available columns:** {', '.join(df_info.get('columns', [])[:8])}
""",
                'insights': "Couldn't generate plan. Try being more specific.",
                'suggestions': self._get_suggestions()
            }
        
        # Validate code safety
        is_safe, safety_msg = self._is_code_safe(generated['code'])
        
        if not is_safe:
            self._reset_state()
            return {
                'content': f"""## ⚠️ Safety Check Failed

The generated code didn't pass safety validation.

**Reason:** {safety_msg}

Please try a different question.
""",
                'insights': "Code safety check failed.",
                'suggestions': self._get_suggestions()
            }
        
        # Store the plan
        st.session_state.dynamic_state = self.STATE_PLANNED
        st.session_state.dynamic_plan = generated.get('plan', '')
        st.session_state.dynamic_code = generated.get('code', '')
        
        content = f"""## 🔮 Analysis Plan Ready

**Your request:** "{query}"

---

### 📋 My Plan:

{generated.get('plan', 'Analyze the data as requested')}

---

### 🔧 Generated Code:

```python
{generated.get('code', '')}
```

---

{f"### 💡 Expected Result:" + chr(10) + generated.get('explanation', '') if generated.get('explanation') else ''}

---

### ⚡ Ready to execute this code?

**Type `yes` to run** or `no` to cancel.

*The code will run on a copy of your data - your original data is safe.*
"""
        
        return {
            'content': content,
            'insights': "⏳ **Step 2 of 3** - Review the plan and type 'yes' to execute.",
            'suggestions': ["yes", "no"]
        }
    
    def _step3_execute(self) -> Dict[str, Any]:
        """
        STEP 3: Execute the code and show results.
        """
        query = st.session_state.dynamic_query
        code = st.session_state.dynamic_code
        
        # Reset state before execution
        self._reset_state()
        
        # Execute
        exec_result = self._execute_code(code, self.analyzer.df)
        
        if not exec_result['success']:
            error_analysis = ""
            if self.llm and self.llm.is_active():
                error_analysis = self.llm.analyze_error(code, exec_result['error'], query) or ""
            
            return {
                'content': f"""## ⚠️ Execution Error

**Error:** `{exec_result['error']}`

{f"**Analysis:** {error_analysis}" if error_analysis else ""}

### What to try:
- Check if column names are correct
- Rephrase your question more specifically
- Try a simpler version of the analysis

<details>
<summary>🔧 View Code That Failed</summary>

```python
{code}
```
</details>
""",
                'figure': None,
                'dataframe': None,
                'insights': "⚠️ Execution failed. Try rephrasing your question.",
                'suggestions': self._get_suggestions()
            }
        
        # Format successful result
        result = exec_result.get('result')
        result_df = exec_result.get('result_df')
        fig = exec_result.get('fig')
        
        content = f"""## ✅ Analysis Complete!

**Your request:** "{query}"

---

### 📊 Result:

{self._format_result(result) if result is not None else ""}
{self._format_result(result_df) if result_df is not None and result is None else ""}

---

<details>
<summary>🔧 View Generated Code</summary>

```python
{code}
```
</details>
"""
        
        return {
            'content': content,
            'figure': fig,
            'dataframe': result_df if isinstance(result_df, pd.DataFrame) else None,
            'insights': "✅ **Dynamic Analysis Complete** - Custom code executed successfully!",
            'suggestions': self._get_suggestions()
        }
    
    def process(self, query: str) -> Dict[str, Any]:
        """
        Main process function - handles the 3-step flow.
        """
        self._init_state()
        
        # Check prerequisites
        if self.analyzer is None or self.analyzer.df is None:
            return {
                'content': "## ⚠️ No Data Loaded\n\nPlease load a dataset first.",
                'insights': "Load data to use dynamic analysis.",
                'suggestions': ["📂 Load Fitness Data", "📂 Load E-commerce Data"]
            }
        
        current_state = st.session_state.dynamic_state
        is_confirm = self._is_confirmation(query)
        
        # Handle based on current state
        if current_state == self.STATE_OFFERED:
            # User was offered, waiting for yes/no
            if is_confirm is True:
                # User said YES to offer → Generate plan (Step 2)
                return self._step2_plan(st.session_state.dynamic_query)
            elif is_confirm is False:
                # User said NO → Cancel
                self._reset_state()
                return {
                    'content': "## ❌ Cancelled\n\nNo problem! Let me know if you want to try something else.",
                    'insights': "Analysis cancelled.",
                    'suggestions': self._get_suggestions()
                }
            else:
                # User typed something else → Treat as new query
                self._reset_state()
                return self._step1_offer(query)
        
        elif current_state == self.STATE_PLANNED:
            # Plan was shown, waiting for yes/no
            if is_confirm is True:
                # User said YES to execute → Run code (Step 3)
                return self._step3_execute()
            elif is_confirm is False:
                # User said NO → Cancel
                self._reset_state()
                return {
                    'content': "## ❌ Cancelled\n\nNo problem! The code was not executed. Let me know if you want to try something else.",
                    'insights': "Execution cancelled. Your data was not modified.",
                    'suggestions': self._get_suggestions()
                }
            else:
                # User typed something else → Treat as new query
                self._reset_state()
                return self._step1_offer(query)
        
        else:
            # IDLE state → Start new flow (Step 1)
            return self._step1_offer(query)
    
    def _get_suggestions(self) -> list:
        """Get contextual suggestions."""
        suggestions = ["📊 Show statistics", "📈 Correlation heatmap"]
        
        if self.analyzer and self.analyzer.df is not None:
            cols = self.analyzer.df.columns.tolist()
            if len(cols) >= 2:
                suggestions.append(f"📈 Scatter {cols[0]} vs {cols[1]}")
            if self.analyzer.usable_numeric:
                suggestions.append(f"📊 Histogram {self.analyzer.usable_numeric[0]}")
        
        suggestions.extend(["🆘 Help", "ℹ️ About"])
        return suggestions[:6]


# Convenience function
def create_dynamic_agent(analyzer=None, llm=None) -> DynamicAgent:
    """Create a configured Dynamic Agent."""
    return DynamicAgent(analyzer=analyzer, llm=llm)
