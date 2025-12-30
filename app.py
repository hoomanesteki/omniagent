"""
🤖 OmniAgent - Your AI Data Analysis Assistant

A friendly, intuitive data analysis tool that helps you:
- Explore your data with natural language
- Create beautiful visualizations  
- Run statistical analysis
- Build simple prediction models

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import io
import base64
from datetime import datetime

# Page config
st.set_page_config(
    page_title="🤖 OmniAgent - AI Data Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .stButton>button {
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'df': None,
        'filename': None,
        'chat_history': [],
        'current_step': 'welcome',  # welcome, data_loaded, exploring, analyzing
        'eda_done': False,
        'model_trained': False,
        'trained_model': None,
        'target_column': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_column_types(df):
    """Categorize columns by type."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    return numeric_cols, categorical_cols, datetime_cols


def add_chat_message(role, content, msg_type="text"):
    """Add message to chat history."""
    st.session_state.chat_history.append({
        'role': role,
        'content': content,
        'type': msg_type,
        'time': datetime.now().strftime("%H:%M")
    })


def format_number(num):
    """Format large numbers nicely."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data(uploaded_file=None, sample_name=None):
    """Load data from upload or sample."""
    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            filename = uploaded_file.name
        elif sample_name:
            path = Path(f"data/samples/{sample_name}")
            df = pd.read_csv(path)
            filename = sample_name
        else:
            return None, None
        
        st.session_state.df = df
        st.session_state.filename = filename
        st.session_state.current_step = 'data_loaded'
        st.session_state.eda_done = False
        st.session_state.model_trained = False
        
        return df, filename
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        return None, None


# ============================================================================
# EDA FUNCTIONS
# ============================================================================

def show_quick_eda(df):
    """Show quick EDA summary."""
    st.markdown("### 📊 Quick Data Overview")
    
    numeric_cols, categorical_cols, datetime_cols = get_column_types(df)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Rows", format_number(len(df)))
    with col2:
        st.metric("📊 Columns", len(df.columns))
    with col3:
        st.metric("🔢 Numeric", len(numeric_cols))
    with col4:
        st.metric("📝 Categorical", len(categorical_cols))
    
    # Missing values summary
    missing = df.isnull().sum()
    total_missing = missing.sum()
    
    if total_missing > 0:
        st.markdown(f"""
        <div class="warning-box">
            ⚠️ <strong>Missing Values Detected:</strong> {total_missing} total missing values across {(missing > 0).sum()} columns
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-box">
            ✅ <strong>No Missing Values!</strong> Your data is complete.
        </div>
        """, unsafe_allow_html=True)
    
    # Data types table
    with st.expander("📋 Column Details", expanded=False):
        col_info = pd.DataFrame({
            'Column': df.columns,
            'Type': df.dtypes.astype(str),
            'Non-Null': df.count(),
            'Null': df.isnull().sum(),
            'Unique': df.nunique()
        })
        st.dataframe(col_info, use_container_width=True, hide_index=True)
    
    # Sample data
    with st.expander("👀 Sample Data (First 5 rows)", expanded=True):
        st.dataframe(df.head(), use_container_width=True)
    
    return numeric_cols, categorical_cols


def show_detailed_eda(df):
    """Show detailed EDA with visualizations."""
    st.markdown("### 🔍 Detailed Exploratory Data Analysis")
    
    numeric_cols, categorical_cols, _ = get_column_types(df)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Distributions", 
        "🔗 Correlations", 
        "📊 Categories", 
        "❓ Missing Values"
    ])
    
    with tab1:
        if numeric_cols:
            st.markdown("#### 📈 Numeric Column Distributions")
            selected_num = st.selectbox(
                "Select column to visualize:",
                numeric_cols,
                key="dist_col"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Histogram with Plotly
                fig = px.histogram(
                    df, x=selected_num, 
                    title=f"Distribution of {selected_num}",
                    template="plotly_white",
                    color_discrete_sequence=['#667eea']
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Box plot
                fig = px.box(
                    df, y=selected_num,
                    title=f"Box Plot of {selected_num}",
                    template="plotly_white",
                    color_discrete_sequence=['#764ba2']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Statistics
            stats = df[selected_num].describe()
            st.markdown("**📊 Statistics:**")
            stat_cols = st.columns(6)
            stat_names = ['count', 'mean', 'std', 'min', '50%', 'max']
            for i, stat in enumerate(stat_names):
                with stat_cols[i]:
                    st.metric(stat.capitalize(), f"{stats[stat]:.2f}")
        else:
            st.info("No numeric columns found for distribution analysis.")
    
    with tab2:
        if len(numeric_cols) >= 2:
            st.markdown("#### 🔗 Correlation Analysis")
            
            # Correlation matrix
            corr_matrix = df[numeric_cols].corr()
            
            fig = px.imshow(
                corr_matrix,
                labels=dict(color="Correlation"),
                x=numeric_cols,
                y=numeric_cols,
                color_continuous_scale="RdBu_r",
                title="Correlation Heatmap",
                template="plotly_white"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Top correlations
            st.markdown("**🔝 Top Correlations:**")
            corr_pairs = []
            for i in range(len(numeric_cols)):
                for j in range(i+1, len(numeric_cols)):
                    corr_pairs.append({
                        'Column 1': numeric_cols[i],
                        'Column 2': numeric_cols[j],
                        'Correlation': corr_matrix.iloc[i, j]
                    })
            corr_df = pd.DataFrame(corr_pairs).sort_values('Correlation', key=abs, ascending=False)
            st.dataframe(corr_df.head(10), use_container_width=True, hide_index=True)
            
            # Scatter plot
            st.markdown("#### 📊 Scatter Plot")
            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox("X-axis:", numeric_cols, key="scatter_x")
            with col2:
                y_col = st.selectbox("Y-axis:", numeric_cols, index=min(1, len(numeric_cols)-1), key="scatter_y")
            
            color_col = None
            if categorical_cols:
                color_col = st.selectbox("Color by (optional):", [None] + categorical_cols, key="scatter_color")
            
            fig = px.scatter(
                df, x=x_col, y=y_col, color=color_col,
                title=f"{x_col} vs {y_col}",
                template="plotly_white",
                trendline="ols" if color_col is None else None
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need at least 2 numeric columns for correlation analysis.")
    
    with tab3:
        if categorical_cols:
            st.markdown("#### 📊 Categorical Column Analysis")
            selected_cat = st.selectbox(
                "Select categorical column:",
                categorical_cols,
                key="cat_col"
            )
            
            value_counts = df[selected_cat].value_counts().head(15)
            
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"Distribution of {selected_cat} (Top 15)",
                labels={'x': selected_cat, 'y': 'Count'},
                template="plotly_white",
                color_discrete_sequence=['#667eea']
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Value counts table
            st.markdown(f"**📋 Value Counts for {selected_cat}:**")
            vc_df = pd.DataFrame({
                'Value': value_counts.index,
                'Count': value_counts.values,
                'Percentage': (value_counts.values / len(df) * 100).round(2)
            })
            st.dataframe(vc_df, use_container_width=True, hide_index=True)
        else:
            st.info("No categorical columns found.")
    
    with tab4:
        st.markdown("#### ❓ Missing Values Analysis")
        
        missing = df.isnull().sum()
        missing_df = pd.DataFrame({
            'Column': missing.index,
            'Missing Count': missing.values,
            'Missing %': (missing.values / len(df) * 100).round(2)
        }).sort_values('Missing Count', ascending=False)
        
        missing_df = missing_df[missing_df['Missing Count'] > 0]
        
        if len(missing_df) > 0:
            fig = px.bar(
                missing_df,
                x='Column',
                y='Missing %',
                title="Missing Values by Column",
                template="plotly_white",
                color='Missing %',
                color_continuous_scale='Reds'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(missing_df, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 No missing values in this dataset!")
    
    st.session_state.eda_done = True


# ============================================================================
# STATISTICS FUNCTIONS
# ============================================================================

def show_statistics(df):
    """Show detailed statistics."""
    st.markdown("### 📊 Statistical Analysis")
    
    numeric_cols, categorical_cols, _ = get_column_types(df)
    
    tab1, tab2, tab3 = st.tabs(["📈 Descriptive Stats", "📊 Group Analysis", "🎯 Outliers"])
    
    with tab1:
        if numeric_cols:
            st.markdown("#### 📈 Descriptive Statistics")
            stats_df = df[numeric_cols].describe().T
            stats_df['skewness'] = df[numeric_cols].skew()
            stats_df['kurtosis'] = df[numeric_cols].kurtosis()
            st.dataframe(stats_df.round(3), use_container_width=True)
        else:
            st.info("No numeric columns for statistics.")
    
    with tab2:
        if categorical_cols and numeric_cols:
            st.markdown("#### 📊 Group-By Analysis")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                group_col = st.selectbox("Group by:", categorical_cols, key="group_col")
            with col2:
                agg_col = st.selectbox("Aggregate:", numeric_cols, key="agg_col")
            with col3:
                agg_func = st.selectbox("Function:", ["mean", "sum", "count", "median", "min", "max"], key="agg_func")
            
            grouped = df.groupby(group_col)[agg_col].agg(agg_func).reset_index()
            grouped.columns = [group_col, f"{agg_func}_{agg_col}"]
            grouped = grouped.sort_values(f"{agg_func}_{agg_col}", ascending=False)
            
            fig = px.bar(
                grouped.head(20),
                x=group_col,
                y=f"{agg_func}_{agg_col}",
                title=f"{agg_func.capitalize()} of {agg_col} by {group_col}",
                template="plotly_white",
                color_discrete_sequence=['#667eea']
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(grouped.head(20), use_container_width=True, hide_index=True)
        else:
            st.info("Need both categorical and numeric columns for group analysis.")
    
    with tab3:
        if numeric_cols:
            st.markdown("#### 🎯 Outlier Detection")
            
            outlier_col = st.selectbox("Select column:", numeric_cols, key="outlier_col")
            method = st.radio("Method:", ["IQR", "Z-Score"], horizontal=True)
            
            data = df[outlier_col].dropna()
            
            if method == "IQR":
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                outliers = data[(data < lower) | (data > upper)]
                
                st.markdown(f"""
                **IQR Method Results:**
                - Q1: {Q1:.2f}
                - Q3: {Q3:.2f}
                - IQR: {IQR:.2f}
                - Lower bound: {lower:.2f}
                - Upper bound: {upper:.2f}
                - **Outliers found: {len(outliers)} ({len(outliers)/len(data)*100:.1f}%)**
                """)
            else:
                mean = data.mean()
                std = data.std()
                z_scores = np.abs((data - mean) / std)
                outliers = data[z_scores > 3]
                
                st.markdown(f"""
                **Z-Score Method Results (|z| > 3):**
                - Mean: {mean:.2f}
                - Std: {std:.2f}
                - **Outliers found: {len(outliers)} ({len(outliers)/len(data)*100:.1f}%)**
                """)
            
            # Box plot with outliers highlighted
            fig = px.box(df, y=outlier_col, title=f"Outliers in {outlier_col}", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# PREDICTION FUNCTIONS
# ============================================================================

def show_prediction(df):
    """Simple prediction model builder."""
    st.markdown("### 🎯 Build a Prediction Model")
    
    st.markdown("""
    <div class="info-box">
        💡 <strong>How it works:</strong> Select a target column to predict, choose feature columns, 
        and I'll train a simple model for you!
    </div>
    """, unsafe_allow_html=True)
    
    numeric_cols, categorical_cols, _ = get_column_types(df)
    
    if len(numeric_cols) < 2:
        st.warning("⚠️ Need at least 2 numeric columns for prediction.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        target = st.selectbox(
            "🎯 Select target column (what to predict):",
            numeric_cols,
            key="target_col"
        )
    
    with col2:
        available_features = [c for c in numeric_cols if c != target]
        features = st.multiselect(
            "📊 Select feature columns:",
            available_features,
            default=available_features[:min(3, len(available_features))],
            key="feature_cols"
        )
    
    if not features:
        st.warning("⚠️ Please select at least one feature column.")
        return
    
    model_type = st.radio(
        "Select model type:",
        ["Linear Regression", "Random Forest", "Gradient Boosting"],
        horizontal=True
    )
    
    if st.button("🚀 Train Model", type="primary"):
        with st.spinner("Training model..."):
            try:
                from sklearn.model_selection import train_test_split
                from sklearn.linear_model import LinearRegression
                from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
                from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
                from sklearn.preprocessing import StandardScaler
                
                # Prepare data
                X = df[features].dropna()
                y = df.loc[X.index, target]
                
                # Split
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                # Scale
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train
                if model_type == "Linear Regression":
                    model = LinearRegression()
                elif model_type == "Random Forest":
                    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
                else:
                    model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
                
                model.fit(X_train_scaled, y_train)
                
                # Predict
                y_pred = model.predict(X_test_scaled)
                
                # Metrics
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                st.session_state.trained_model = {
                    'model': model,
                    'scaler': scaler,
                    'features': features,
                    'target': target,
                    'metrics': {'RMSE': rmse, 'MAE': mae, 'R²': r2}
                }
                st.session_state.model_trained = True
                st.session_state.target_column = target
                
                # Show results
                st.markdown("### ✅ Model Trained Successfully!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📏 RMSE", f"{rmse:.3f}")
                with col2:
                    st.metric("📐 MAE", f"{mae:.3f}")
                with col3:
                    st.metric("📊 R² Score", f"{r2:.3f}")
                
                # Actual vs Predicted plot
                fig = px.scatter(
                    x=y_test, y=y_pred,
                    labels={'x': 'Actual', 'y': 'Predicted'},
                    title="Actual vs Predicted Values",
                    template="plotly_white"
                )
                fig.add_trace(go.Scatter(
                    x=[y_test.min(), y_test.max()],
                    y=[y_test.min(), y_test.max()],
                    mode='lines',
                    name='Perfect Prediction',
                    line=dict(color='red', dash='dash')
                ))
                st.plotly_chart(fig, use_container_width=True)
                
                # Feature importance (for tree models)
                if model_type != "Linear Regression":
                    importance = pd.DataFrame({
                        'Feature': features,
                        'Importance': model.feature_importances_
                    }).sort_values('Importance', ascending=True)
                    
                    fig = px.bar(
                        importance, x='Importance', y='Feature',
                        orientation='h',
                        title="Feature Importance",
                        template="plotly_white",
                        color='Importance',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error training model: {e}")
    
    # Prediction interface
    if st.session_state.model_trained and st.session_state.trained_model:
        st.markdown("---")
        st.markdown("### 🔮 Make Predictions")
        
        model_info = st.session_state.trained_model
        
        st.markdown("Enter values for each feature:")
        
        input_values = {}
        cols = st.columns(min(len(model_info['features']), 3))
        for i, feat in enumerate(model_info['features']):
            with cols[i % 3]:
                default_val = float(df[feat].median())
                input_values[feat] = st.number_input(
                    f"{feat}:",
                    value=default_val,
                    key=f"pred_{feat}"
                )
        
        if st.button("🎯 Predict", type="secondary"):
            input_df = pd.DataFrame([input_values])
            input_scaled = model_info['scaler'].transform(input_df)
            prediction = model_info['model'].predict(input_scaled)[0]
            
            st.markdown(f"""
            <div class="success-box">
                🎯 <strong>Predicted {model_info['target']}:</strong> {prediction:.2f}
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def show_visualizations(df):
    """Create custom visualizations."""
    st.markdown("### 📊 Create Visualizations")
    
    numeric_cols, categorical_cols, _ = get_column_types(df)
    
    chart_type = st.selectbox(
        "Select chart type:",
        ["📊 Histogram", "📈 Line Chart", "🔵 Scatter Plot", "📦 Box Plot", 
         "🥧 Pie Chart", "🔥 Heatmap", "📊 Bar Chart"]
    )
    
    if chart_type == "📊 Histogram":
        if numeric_cols:
            col = st.selectbox("Select column:", numeric_cols)
            bins = st.slider("Number of bins:", 10, 100, 30)
            
            fig = px.histogram(
                df, x=col, nbins=bins,
                title=f"Histogram of {col}",
                template="plotly_white",
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "📈 Line Chart":
        if numeric_cols:
            y_col = st.selectbox("Y-axis:", numeric_cols)
            fig = px.line(
                df.reset_index(), x='index', y=y_col,
                title=f"Line Chart of {y_col}",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "🔵 Scatter Plot":
        if len(numeric_cols) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox("X-axis:", numeric_cols)
            with col2:
                y_col = st.selectbox("Y-axis:", numeric_cols, index=1)
            
            color = None
            if categorical_cols:
                color = st.selectbox("Color by:", [None] + categorical_cols)
            
            fig = px.scatter(
                df, x=x_col, y=y_col, color=color,
                title=f"{x_col} vs {y_col}",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "📦 Box Plot":
        if numeric_cols:
            num_col = st.selectbox("Numeric column:", numeric_cols)
            group_col = None
            if categorical_cols:
                group_col = st.selectbox("Group by (optional):", [None] + categorical_cols)
            
            fig = px.box(
                df, y=num_col, x=group_col,
                title=f"Box Plot of {num_col}",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "🥧 Pie Chart":
        if categorical_cols:
            col = st.selectbox("Select column:", categorical_cols)
            
            value_counts = df[col].value_counts().head(10)
            fig = px.pie(
                values=value_counts.values,
                names=value_counts.index,
                title=f"Distribution of {col}",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "🔥 Heatmap":
        if len(numeric_cols) >= 2:
            selected = st.multiselect(
                "Select columns:",
                numeric_cols,
                default=numeric_cols[:min(8, len(numeric_cols))]
            )
            if len(selected) >= 2:
                corr = df[selected].corr()
                fig = px.imshow(
                    corr,
                    labels=dict(color="Correlation"),
                    color_continuous_scale="RdBu_r",
                    title="Correlation Heatmap",
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "📊 Bar Chart":
        if categorical_cols:
            cat_col = st.selectbox("Category column:", categorical_cols)
            
            if numeric_cols:
                agg_col = st.selectbox("Aggregate column:", [None] + numeric_cols)
                agg_func = st.selectbox("Function:", ["count", "mean", "sum", "median"])
                
                if agg_col and agg_func != "count":
                    data = df.groupby(cat_col)[agg_col].agg(agg_func).reset_index()
                    data.columns = [cat_col, agg_col]
                    fig = px.bar(
                        data.head(20), x=cat_col, y=agg_col,
                        title=f"{agg_func.capitalize()} of {agg_col} by {cat_col}",
                        template="plotly_white"
                    )
                else:
                    data = df[cat_col].value_counts().head(20).reset_index()
                    data.columns = [cat_col, 'count']
                    fig = px.bar(
                        data, x=cat_col, y='count',
                        title=f"Count by {cat_col}",
                        template="plotly_white"
                    )
            else:
                data = df[cat_col].value_counts().head(20).reset_index()
                data.columns = [cat_col, 'count']
                fig = px.bar(
                    data, x=cat_col, y='count',
                    title=f"Count by {cat_col}",
                    template="plotly_white"
                )
            
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# SIDEBAR
# ============================================================================

def render_sidebar():
    """Render sidebar with navigation and options."""
    with st.sidebar:
        st.markdown('<p class="main-header">🤖 OmniAgent</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Your AI Data Analysis Assistant</p>', unsafe_allow_html=True)
        
        st.divider()
        
        # Data loading section
        st.markdown("### 📁 Load Data")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=['csv'],
            help="Upload a CSV file to analyze"
        )
        
        if uploaded_file:
            if st.button("📤 Load Uploaded File", type="primary", use_container_width=True):
                load_data(uploaded_file=uploaded_file)
                st.rerun()
        
        # Sample datasets
        st.markdown("**Or try a sample dataset:**")
        
        samples_dir = Path("data/samples")
        if samples_dir.exists():
            sample_files = list(samples_dir.glob("*.csv"))
            if sample_files:
                for sample in sample_files:
                    emoji = "📊"
                    if "fitness" in sample.name.lower():
                        emoji = "🏃"
                    elif "ecommerce" in sample.name.lower() or "sales" in sample.name.lower():
                        emoji = "🛒"
                    elif "airbnb" in sample.name.lower():
                        emoji = "🏠"
                    
                    if st.button(f"{emoji} {sample.stem}", key=f"sample_{sample.name}", use_container_width=True):
                        load_data(sample_name=sample.name)
                        st.rerun()
        
        # Current data info
        if st.session_state.df is not None:
            st.divider()
            st.markdown("### 📋 Current Data")
            st.success(f"✅ **{st.session_state.filename}**")
            st.markdown(f"""
            - 📝 **Rows:** {len(st.session_state.df):,}
            - 📊 **Columns:** {len(st.session_state.df.columns)}
            """)
            
            if st.button("🗑️ Clear Data", use_container_width=True):
                for key in ['df', 'filename', 'chat_history', 'eda_done', 'model_trained', 'trained_model']:
                    if key in st.session_state:
                        st.session_state[key] = None if key != 'chat_history' else []
                st.session_state.current_step = 'welcome'
                st.rerun()
        
        # Help section
        st.divider()
        st.markdown("### ❓ Need Help?")
        st.markdown("""
        **What you can do:**
        - 📊 Explore data distributions
        - 🔗 Find correlations
        - 📈 Create visualizations
        - 📉 Detect outliers
        - 🎯 Build prediction models
        """)


# ============================================================================
# MAIN CONTENT
# ============================================================================

def show_welcome():
    """Show welcome screen."""
    st.markdown('<p class="main-header">🤖 Welcome to OmniAgent!</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your friendly AI-powered data analysis assistant</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 👋 Hi there! I'm OmniAgent
        
        I'm here to help you **explore, analyze, and understand your data** - no coding required!
        
        #### 🚀 Here's what I can do for you:
        
        | Feature | Description |
        |---------|-------------|
        | 📊 **Quick Overview** | Instantly see key stats about your data |
        | 🔍 **Detailed EDA** | Explore distributions, correlations & patterns |
        | 📈 **Visualizations** | Create beautiful charts with one click |
        | 📉 **Statistics** | Run group-by analysis & detect outliers |
        | 🎯 **Predictions** | Build simple ML models to predict values |
        
        #### 🏁 Getting Started
        
        1. **Upload your CSV file** using the sidebar, OR
        2. **Try a sample dataset** to explore the features
        3. **Follow the guided tabs** to analyze your data step by step
        
        """)
    
    with col2:
        st.markdown("""
        <div class="info-box">
        <h4>💡 Tips</h4>
        <ul>
            <li>Start with Quick Overview</li>
            <li>Check for missing values</li>
            <li>Explore correlations</li>
            <li>Try building a model!</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="success-box">
        <h4>📂 Sample Datasets</h4>
        <ul>
            <li>🏃 Fitness Tracker</li>
            <li>🛒 E-commerce Sales</li>
            <li>🏠 NYC Airbnb</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)


def show_main_content():
    """Show main content area."""
    df = st.session_state.df
    
    if df is None:
        show_welcome()
        return
    
    # Header with data info
    st.markdown(f'<p class="main-header">📊 Analyzing: {st.session_state.filename}</p>', unsafe_allow_html=True)
    
    # Create tabs for different analysis types
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Overview",
        "🔍 Detailed EDA", 
        "📊 Visualizations",
        "📈 Statistics",
        "🎯 Predictions"
    ])
    
    with tab1:
        show_quick_eda(df)
        
        st.markdown("---")
        st.markdown("""
        <div class="info-box">
        <h4>👉 Next Steps</h4>
        <p>Now that you've seen the overview, explore the other tabs:</p>
        <ul>
            <li><strong>🔍 Detailed EDA</strong> - Deep dive into distributions and correlations</li>
            <li><strong>📊 Visualizations</strong> - Create custom charts</li>
            <li><strong>📈 Statistics</strong> - Run group analysis and find outliers</li>
            <li><strong>🎯 Predictions</strong> - Build a simple prediction model</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        show_detailed_eda(df)
    
    with tab3:
        show_visualizations(df)
    
    with tab4:
        show_statistics(df)
    
    with tab5:
        show_prediction(df)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main application."""
    init_session_state()
    render_sidebar()
    show_main_content()


if __name__ == "__main__":
    main()
