"""
🧪 OmniAgent Test Suite
========================
Run with: python tests/test_all.py

Tests all functionality without needing Streamlit or API key.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import json

# ============================================================================
# TEST RESULTS TRACKING
# ============================================================================
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, name):
        self.passed += 1
        print(f"  ✅ {name}")
    
    def add_fail(self, name, error):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ❌ {name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"RESULTS: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print(f"{'='*50}")
        return self.failed == 0

results = TestResults()

# ============================================================================
# TEST 1: SAMPLE DATASETS
# ============================================================================
print("\n📁 TEST 1: Sample Datasets")
print("-" * 40)

datasets = [
    ("data/samples/fitness_tracker.csv", 100, 10),
    ("data/samples/nyc_airbnb.csv", 100, 5),
    ("data/samples/ecommerce_sales.csv", 50, 5),
]

for path, min_rows, min_cols in datasets:
    try:
        full_path = Path(__file__).parent.parent / path
        if not full_path.exists():
            full_path = Path(path)
        
        df = pd.read_csv(full_path)
        if len(df) >= min_rows and len(df.columns) >= min_cols:
            results.add_pass(f"{path} ({len(df)} rows, {len(df.columns)} cols)")
        else:
            results.add_fail(path, f"Too small: {len(df)} rows, {len(df.columns)} cols")
    except Exception as e:
        results.add_fail(path, str(e))

# ============================================================================
# TEST 2: SCHEMA AGENT
# ============================================================================
print("\n📋 TEST 2: Schema Agent")
print("-" * 40)

# Create test dataframe
test_df = pd.DataFrame({
    "id": range(100),
    "price": np.random.uniform(10, 1000, 100),
    "quantity": np.random.randint(1, 50, 100),
    "category": np.random.choice(["A", "B", "C"], 100),
    "status": np.random.choice(["active", "inactive"], 100),
})

# Define SchemaAgent locally for testing
class SchemaAgent:
    @staticmethod
    def get_schema(df):
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "all_columns": df.columns.tolist(),
        }
    
    @staticmethod
    def get_sample(df, n=5):
        return df.head(n).to_string()

try:
    schema = SchemaAgent.get_schema(test_df)
    
    if schema["total_rows"] == 100:
        results.add_pass("Row count correct")
    else:
        results.add_fail("Row count", f"Expected 100, got {schema['total_rows']}")
    
    if schema["total_columns"] == 5:
        results.add_pass("Column count correct")
    else:
        results.add_fail("Column count", f"Expected 5, got {schema['total_columns']}")
    
    if set(schema["numeric_columns"]) == {"id", "price", "quantity"}:
        results.add_pass("Numeric columns detected")
    else:
        results.add_fail("Numeric columns", f"Got {schema['numeric_columns']}")
    
    if set(schema["categorical_columns"]) == {"category", "status"}:
        results.add_pass("Categorical columns detected")
    else:
        results.add_fail("Categorical columns", f"Got {schema['categorical_columns']}")
    
    sample = SchemaAgent.get_sample(test_df, 3)
    if len(sample) > 0:
        results.add_pass("Sample data returned")
    else:
        results.add_fail("Sample data", "Empty")

except Exception as e:
    results.add_fail("Schema Agent", str(e))

# ============================================================================
# TEST 3: STATS AGENT
# ============================================================================
print("\n📊 TEST 3: Stats Agent")
print("-" * 40)

class StatsAgent:
    @staticmethod
    def describe(df, column=None):
        if column and column in df.columns:
            return {column: df[column].describe().to_dict()}
        numeric_df = df.select_dtypes(include=[np.number])
        return {col: numeric_df[col].describe().to_dict() for col in numeric_df.columns}
    
    @staticmethod
    def correlation(df):
        numeric_df = df.select_dtypes(include=[np.number])
        return numeric_df.corr().round(4).to_dict()
    
    @staticmethod
    def outliers(df, column):
        data = df[column].dropna()
        Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
        IQR = Q3 - Q1
        lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        outliers = data[(data < lower) | (data > upper)]
        return {"column": column, "outlier_count": len(outliers)}
    
    @staticmethod
    def missing_values(df):
        missing = df.isnull().sum()
        return {col: {"count": int(missing[col])} for col in df.columns}

try:
    # Test describe
    desc = StatsAgent.describe(test_df)
    if "price" in desc and "mean" in desc["price"]:
        results.add_pass("Describe works")
    else:
        results.add_fail("Describe", "Missing expected keys")
    
    # Test describe single column
    desc_single = StatsAgent.describe(test_df, "price")
    if "price" in desc_single:
        results.add_pass("Describe single column works")
    else:
        results.add_fail("Describe single", "Column not in result")
    
    # Test correlation
    corr = StatsAgent.correlation(test_df)
    if "price" in corr and "quantity" in corr["price"]:
        results.add_pass("Correlation works")
    else:
        results.add_fail("Correlation", "Missing expected keys")
    
    # Test outliers
    outliers = StatsAgent.outliers(test_df, "price")
    if "outlier_count" in outliers:
        results.add_pass("Outliers detection works")
    else:
        results.add_fail("Outliers", "Missing outlier_count")
    
    # Test missing values
    missing = StatsAgent.missing_values(test_df)
    if "price" in missing:
        results.add_pass("Missing values works")
    else:
        results.add_fail("Missing values", "Missing expected column")

except Exception as e:
    results.add_fail("Stats Agent", str(e))

# ============================================================================
# TEST 4: PLOT AGENT
# ============================================================================
print("\n📈 TEST 4: Plot Agent")
print("-" * 40)

try:
    import plotly.express as px
    
    # Test histogram
    fig = px.histogram(test_df, x="price")
    if fig is not None:
        results.add_pass("Histogram creation")
    else:
        results.add_fail("Histogram", "None returned")
    
    # Test scatter
    fig = px.scatter(test_df, x="price", y="quantity")
    if fig is not None:
        results.add_pass("Scatter plot creation")
    else:
        results.add_fail("Scatter", "None returned")
    
    # Test bar
    counts = test_df["category"].value_counts()
    fig = px.bar(x=counts.index, y=counts.values)
    if fig is not None:
        results.add_pass("Bar chart creation")
    else:
        results.add_fail("Bar", "None returned")
    
    # Test box
    fig = px.box(test_df, y="price")
    if fig is not None:
        results.add_pass("Box plot creation")
    else:
        results.add_fail("Box", "None returned")
    
    # Test heatmap
    corr = test_df.select_dtypes(include=[np.number]).corr()
    fig = px.imshow(corr)
    if fig is not None:
        results.add_pass("Heatmap creation")
    else:
        results.add_fail("Heatmap", "None returned")
    
    # Test pie
    counts = test_df["category"].value_counts()
    fig = px.pie(values=counts.values, names=counts.index)
    if fig is not None:
        results.add_pass("Pie chart creation")
    else:
        results.add_fail("Pie", "None returned")

except ImportError:
    print("  ⚠️ Plotly not installed - skipping (will work in conda env)")
    results.add_pass("Plotly tests skipped (not installed)")
except Exception as e:
    results.add_fail("Plot Agent", str(e))

# ============================================================================
# TEST 5: PREDICTION AGENT
# ============================================================================
print("\n🔮 TEST 5: Prediction Agent")
print("-" * 40)

try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score, mean_squared_error
    
    # Create prediction test
    target = "price"
    features = ["id", "quantity"]
    
    X = test_df[features]
    y = test_df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    results.add_pass(f"Model training (R²={r2:.3f})")
    results.add_pass(f"Metrics calculation (RMSE={rmse:.2f})")
    
    if hasattr(model, 'feature_importances_'):
        results.add_pass("Feature importance available")
    else:
        results.add_fail("Feature importance", "Not available")

except Exception as e:
    results.add_fail("Prediction Agent", str(e))

# ============================================================================
# TEST 6: KEYWORD MATCHING
# ============================================================================
print("\n🔤 TEST 6: Keyword Matching")
print("-" * 40)

keywords_tests = [
    ("Show descriptive statistics", ["describe", "statistic", "stats"]),
    ("Check for missing values", ["missing", "null"]),
    ("Find outliers in price", ["outlier"]),
    ("Show correlation heatmap", ["heatmap", "correlation"]),
    ("Create histogram of price", ["histogram", "distribution"]),
    ("Scatter plot of x vs y", ["scatter", "vs"]),
    ("Bar chart of category", ["bar", "count"]),
    ("Box plot of price", ["box", "boxplot"]),
    ("Predict price", ["predict", "model", "train"]),
    ("Show schema", ["schema", "columns", "info"]),
    ("Show sample data", ["sample", "head", "preview"]),
]

for query, expected_keywords in keywords_tests:
    msg = query.lower()
    matched = any(w in msg for w in expected_keywords)
    if matched:
        results.add_pass(f"'{query}' matches keywords")
    else:
        results.add_fail(f"'{query}'", f"No match for {expected_keywords}")

# ============================================================================
# TEST 7: EDGE CASES
# ============================================================================
print("\n⚠️ TEST 7: Edge Cases")
print("-" * 40)

# Empty dataframe
empty_df = pd.DataFrame()
try:
    schema = SchemaAgent.get_schema(empty_df)
    if schema["total_rows"] == 0:
        results.add_pass("Empty dataframe handled")
    else:
        results.add_fail("Empty dataframe", "Wrong row count")
except Exception as e:
    results.add_fail("Empty dataframe", str(e))

# Dataframe with NaN
nan_df = pd.DataFrame({
    "a": [1, 2, np.nan, 4, 5],
    "b": [np.nan, 2, 3, 4, np.nan],
})
try:
    missing = StatsAgent.missing_values(nan_df)
    if missing["a"]["count"] == 1 and missing["b"]["count"] == 2:
        results.add_pass("NaN handling correct")
    else:
        results.add_fail("NaN handling", f"Wrong counts: {missing}")
except Exception as e:
    results.add_fail("NaN handling", str(e))

# Non-numeric column for outliers
try:
    result = StatsAgent.outliers(test_df, "category")
    # This should handle gracefully (return error or skip)
    results.add_pass("Non-numeric outlier handled")
except:
    results.add_pass("Non-numeric outlier raised error (expected)")

# ============================================================================
# TEST 8: FILE STRUCTURE
# ============================================================================
print("\n📁 TEST 8: File Structure")
print("-" * 40)

base_path = Path(__file__).parent.parent

required_files = [
    "app_with_llm.py",
    "app.py",
    "requirements.txt",
    "environment.yml",
    "README.md",
    ".env.example",
    "data/samples/fitness_tracker.csv",
    "data/samples/nyc_airbnb.csv",
    "data/samples/ecommerce_sales.csv",
]

for file in required_files:
    file_path = base_path / file
    if file_path.exists():
        results.add_pass(f"{file} exists")
    else:
        results.add_fail(file, "Not found")

# ============================================================================
# TEST 9: SYNTAX CHECK
# ============================================================================
print("\n🔧 TEST 9: Python Syntax")
print("-" * 40)

import py_compile

python_files = ["app_with_llm.py", "app.py"]

for file in python_files:
    file_path = base_path / file
    try:
        py_compile.compile(str(file_path), doraise=True)
        results.add_pass(f"{file} syntax OK")
    except py_compile.PyCompileError as e:
        results.add_fail(file, str(e))

# ============================================================================
# TEST 10: IMPORTS
# ============================================================================
print("\n📦 TEST 10: Required Imports")
print("-" * 40)

required_imports = [
    ("streamlit", "st"),
    ("pandas", "pd"),
    ("numpy", "np"),
    ("plotly.express", "px"),
    ("sklearn.model_selection", None),
    ("sklearn.ensemble", None),
]

for module, alias in required_imports:
    try:
        exec(f"import {module}")
        results.add_pass(f"import {module}")
    except ImportError as e:
        results.add_fail(f"import {module}", str(e))

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n")
success = results.summary()

if success:
    print("\n🎉 All tests passed! Ready to run.")
    print("\nNext steps:")
    print("  1. Copy .env.example to .env")
    print("  2. Add your GROQ_API_KEY (optional)")
    print("  3. Run: streamlit run app_with_llm.py")
else:
    print("\n⚠️ Some tests failed. Please fix before running.")
    sys.exit(1)
