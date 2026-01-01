"""
Prediction Agent Module
=======================
Machine learning model training and evaluation.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

from agents.base import BaseAgent
from core.config import Config


class PredictAgent(BaseAgent):
    """Agent for machine learning predictions - Smart and interactive."""
    
    name = "Prediction Agent"
    emoji = "🤖"
    description = "Machine learning model training and evaluation"
    
    # Patterns for smart understanding
    PREDICT_PATTERNS = {
        'build_model': ['build model', 'create model', 'train model', 'make model', 'build a model'],
        'what_predict': ['what can i predict', 'what to predict', 'suggest target', 'prediction targets'],
        'feature_importance': ['feature importance', 'important features', 'what factors', 'which variables matter'],
        'ml_overview': ['ml overview', 'machine learning', 'model overview', 'prediction overview']
    }
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process prediction-related queries with smart understanding."""
        q = query.lower().strip()
        
        # Check for generic "build model" requests
        if any(p in q for p in self.PREDICT_PATTERNS['build_model']):
            return self._interactive_model_builder()
        
        # Check for "what can I predict"
        if any(p in q for p in self.PREDICT_PATTERNS['what_predict']):
            return self.suggest_targets()
        
        # Check for feature importance without target
        if any(p in q for p in self.PREDICT_PATTERNS['feature_importance']):
            # If no column specified, guide user
            cols = [c for c in self.analyzer.all_columns if c.lower() in q]
            if not cols:
                return self._interactive_model_builder()
        
        # Check for ML overview
        if any(p in q for p in self.PREDICT_PATTERNS['ml_overview']):
            return self._ml_overview()
        
        # Extract target column from query
        cols = [c for c in self.analyzer.all_columns if c.lower() in q]
        
        if cols:
            return self.train(cols[0])
        
        # Default: interactive model builder
        return self._interactive_model_builder()
    
    def _interactive_model_builder(self) -> Dict[str, Any]:
        """Interactive guide for building a model."""
        candidates = self.analyzer.target_candidates
        
        if not candidates:
            return self.format_error("No suitable target columns found for prediction.")
        
        content = f"""## {self.emoji} {self.name} - Model Builder

### 🛠️ Let's Build a Prediction Model!

I'll help you create a machine learning model. First, let's choose what to predict.

---

### 🎯 Available Prediction Targets

Based on your data, here are the best columns to predict:

| # | Column | Type | Why It's Good |
|---|--------|------|---------------|"""
        
        for i, c in enumerate(candidates[:6], 1):
            if c['type'] == 'classification':
                why = f"{c['classes']} distinct categories - good for classification"
            else:
                why = "Continuous numeric values - good for regression"
            content += f"\n| {i} | **{c['column']}** | {c['type'].title()} | {why} |"
        
        content += f"""

---

### 📝 How to Proceed

**Option 1:** Click one of the "Predict [column]" buttons below

**Option 2:** Type "Predict [column name]" (e.g., "Predict {candidates[0]['column']}")

---

### 🔧 What Happens When You Build a Model?

1. **Data Preparation** - I'll handle missing values and scale features
2. **Train/Test Split** - 80% training, 20% testing
3. **Model Training** - Random Forest algorithm
4. **Evaluation** - Accuracy (classification) or R² (regression)
5. **Feature Importance** - Which variables matter most

---

### ℹ️ Model Details

| Setting | Value |
|---------|-------|
| Algorithm | Random Forest |
| Features Used | {len(self.analyzer.usable_numeric)} numeric columns |
| ID Columns Excluded | {', '.join(self.analyzer.id_columns) if self.analyzer.id_columns else 'None'} |
| Missing Values | Auto-imputed with median |
"""
        
        insights = f"""**💡 Ready to Build!**

• I found **{len(candidates)} potential targets** in your data

• **{len(self.analyzer.usable_numeric)} features** will be used as predictors

• Just say "**Predict {candidates[0]['column']}**" to start!

• After building, you'll see model performance and feature importance"""
        
        return {
            'content': content,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def _ml_overview(self) -> Dict[str, Any]:
        """Overview of ML capabilities."""
        content = f"""## {self.emoji} {self.name} - ML Overview

### 🤖 Machine Learning Capabilities

I can build predictive models from your data. Here's what I offer:

---

### 📊 Problem Types

| Type | When to Use | Example |
|------|-------------|---------|
| **Classification** | Predicting categories | Spam/Not Spam, Customer Churn |
| **Regression** | Predicting numbers | Price, Sales, Temperature |

---

### 🔧 Algorithm: Random Forest

I use **Random Forest** because it:
- Works well on most datasets
- Handles missing values
- Provides feature importance
- Doesn't require feature scaling (but I do it anyway)
- Resistant to overfitting

---

### 📈 What You Get

1. **Performance Metrics** - Accuracy or R² score
2. **Confusion Matrix** - For classification models
3. **Actual vs Predicted** - For regression models
4. **Feature Importance** - Which variables matter most

---

### 🎯 Your Data Summary

| Property | Value |
|----------|-------|
| Samples | {self.analyzer.row_count:,} |
| Potential Features | {len(self.analyzer.usable_numeric)} |
| Potential Targets | {len(self.analyzer.target_candidates)} |
| ID Columns (excluded) | {len(self.analyzer.id_columns)} |
"""
        
        return {
            'content': content,
            'insights': "**💡 Tip:** Type 'What can I predict?' to see available targets, or 'Build model' to start the model builder!",
            'suggestions': self.get_suggestions()
        }
    
    def suggest_targets(self) -> Dict[str, Any]:
        """Suggest potential prediction targets."""
        candidates = self.analyzer.target_candidates
        
        if not candidates:
            return self.format_error("No suitable target columns found.")
        
        content = f"""## {self.emoji} {self.name} - Target Selection

### 🎯 What would you like to predict?

Choose a target column based on your analysis goals:

| Column | Type | Details |
|--------|------|---------|"""
        
        for c in candidates[:8]:
            details = f"{c['classes']} classes" if c['type'] == 'classification' else "Continuous"
            content += f"\n| {c['column']} | {c['type'].title()} | {details} |"
        
        content += """

---

### 💡 How to Build a Model

Just say **"Predict [column]"** to build a model!

For example:
- "Predict calories_burned"
- "Predict activity_type"
"""
        
        insights = """**💡 Tips for Choosing a Target:**

• Choose a column that makes **business sense** to predict

• **Classification** targets have discrete categories (e.g., Yes/No, Type A/B/C)

• **Regression** targets are continuous numbers (e.g., price, quantity)

• Ensure enough samples for reliable modeling (>30 recommended)"""
        
        return {
            'content': content,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def train(self, target: str) -> Dict[str, Any]:
        """Train a model to predict the target column."""
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.metrics import accuracy_score, r2_score, mean_absolute_error, confusion_matrix
        
        col = self.find_column(target)
        if not col:
            return self.format_error(f"Column '{target}' not found.")
        
        # Detect problem type
        problem = self.analyzer.detect_problem_type(col)
        
        # Get features (numeric only, exclude target and IDs)
        features = [c for c in self.analyzer.usable_numeric if c != col]
        
        if not features:
            return self.format_error("No numeric features available for modeling.")
        
        # Prepare data
        X = self.df[features].copy().fillna(self.df[features].median())
        y = self.df[col].copy()
        
        # Remove rows with missing target
        mask = ~y.isnull()
        X, y = X[mask], y[mask]
        
        if len(X) < 30:
            return self.format_error("Need at least 30 samples for modeling.")
        
        # Encode target if classification
        le = None
        if problem == "classification":
            le = LabelEncoder()
            y = le.fit_transform(y.astype(str))
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        
        # Train model
        if problem == "classification":
            model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        
        # Evaluate
        if problem == "classification":
            score = accuracy_score(y_test, y_pred)
            cm = confusion_matrix(y_test, y_pred)
            labels = le.classes_ if le else [str(i) for i in range(len(cm))]
            
            fig = px.imshow(
                cm, x=labels, y=labels,
                title=f"🎯 Confusion Matrix: {col}",
                template="plotly_white",
                color_continuous_scale="Blues",
                text_auto=True
            )
            fig.update_layout(xaxis_title="Predicted", yaxis_title="Actual")
            
            quality = "🌟 Excellent" if score >= 0.9 else "✅ Good" if score >= 0.75 else "⚠️ Moderate" if score >= 0.6 else "❌ Poor"
            metric_name = "Accuracy"
            mae = None
        else:
            score = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            fig = px.scatter(
                x=y_test, y=y_pred,
                title=f"🎯 Actual vs Predicted: {col}",
                template="plotly_white",
                color_discrete_sequence=[Config.COLORS[0]]
            )
            fig.add_trace(go.Scatter(
                x=[y_test.min(), y_test.max()],
                y=[y_test.min(), y_test.max()],
                mode='lines',
                name='Perfect',
                line=dict(dash='dash', color='red')
            ))
            
            quality = "🌟 Excellent" if score >= 0.8 else "✅ Good" if score >= 0.6 else "⚠️ Moderate" if score >= 0.3 else "❌ Poor"
            metric_name = "R² Score"
        
        # Feature importance
        imp = pd.DataFrame({
            'Feature': features,
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        content = f"""## {self.emoji} {self.name} - Model Results

### 🎯 Predicting: {col}

**Problem Type:** {problem.title()} | **Model Quality:** {quality}

---

### 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| {metric_name} | {score:.4f} ({score*100:.1f}%) |
| Train Size | {len(X_train):,} |
| Test Size | {len(X_test):,} |
| Features Used | {len(features)} |

---

### 🔑 Top 5 Most Important Features

| Rank | Feature | Importance |
|------|---------|------------|"""
        
        for i, (_, row) in enumerate(imp.head(5).iterrows()):
            content += f"\n| {i+1} | {row['Feature']} | {row['Importance']:.4f} ({row['Importance']*100:.1f}%) |"
        
        if self.analyzer.id_columns:
            content += f"\n\n---\n\n🔑 **Auto-excluded ID columns:** {', '.join(self.analyzer.id_columns)}"
        
        # Build detailed insights
        quality_text = quality.split()[1]
        top_feature = imp.iloc[0]['Feature']
        top_importance = imp.iloc[0]['Importance'] * 100
        top3_features = ', '.join(imp.head(3)['Feature'].tolist())
        
        if problem == "classification":
            insights = f"""**🤖 Model Insights:**

• **Performance Rating:** {quality} - Model achieves {score*100:.1f}% accuracy on test data

• **Top Predictor:** '{top_feature}' contributes {top_importance:.1f}% to predictions

• **Training Details:** Used {len(X_train):,} samples for training, {len(X_test):,} for testing

• **Feature Analysis:** {len(features)} features used, top 3: {top3_features}

• **Recommendation:** {"Model is ready for production use" if score >= 0.75 else "Consider feature engineering or more data to improve accuracy"}"""
        else:
            insights = f"""**🤖 Model Insights:**

• **Performance Rating:** {quality} - Model explains {score*100:.1f}% of variance (R²={score:.3f})

• **Top Predictor:** '{top_feature}' contributes {top_importance:.1f}% to predictions

• **Error Metric:** Mean Absolute Error = {mae:.2f}

• **Training Details:** Used {len(X_train):,} samples for training, {len(X_test):,} for testing

• **Feature Analysis:** {len(features)} features used, top 3: {top3_features}

• **Recommendation:** {"Model is production-ready" if score >= 0.6 else "Consider adding more features or collecting more data"}"""
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def get_suggestions(self) -> List[str]:
        """Get suggestions for predict agent."""
        suggestions = []
        
        for t in self.analyzer.target_candidates[:4]:
            suggestions.append(f"Predict {t['column']}")
        
        while len(suggestions) < 4:
            suggestions.append("What can I predict?")
        
        suggestions.extend([
            "Feature importance",
            "ML overview",
            "Show statistics",
            "Correlation heatmap"
        ])
        
        return suggestions[:8] + ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
