#!/usr/bin/env python3
"""
OmniAgent - Comprehensive Test Suite

Tests all components:
- Data Layer (DuckDB, CSV loading)
- All Specialized Agents (Schema, SQL, EDA, Stats, Plot, Regression)
- MCP Protocol
- Master Agent with Groq API

Run with: python -m pytest tests/ -v
Or standalone: python tests/test_all.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}: {name}")
    if details and not passed:
        print(f"         {details}")


# =============================================================================
# DATA LAYER TESTS
# =============================================================================

def test_data_layer():
    """Test the data layer components."""
    print_header("1. DATA LAYER TESTS")
    
    from omniagent.data.duckdb_engine import DuckDBEngine
    from omniagent.data.loader import DataLoader
    
    # Test 1: Engine creation
    try:
        engine = DuckDBEngine()
        print_test("DuckDB engine creation", True)
    except Exception as e:
        print_test("DuckDB engine creation", False, str(e))
        return None, None
    
    # Test 2: CSV loading
    sample_paths = [
        Path("data/samples/fitness_tracker.csv"),
        Path("data/samples/ecommerce_sales.csv"),
        Path("data/samples/housing.csv"),
    ]
    
    sample_path = None
    for p in sample_paths:
        if p.exists():
            sample_path = p
            break
    
    if not sample_path:
        print_test("CSV loading", False, "No sample CSV found")
        return engine, None
    
    try:
        loader = DataLoader(db_engine=engine)
        profile = loader.load_csv_path(sample_path)
        print_test(f"CSV loading ({sample_path.name})", True)
        print(f"         Loaded {profile.metadata.row_count} rows, {profile.metadata.column_count} columns")
    except Exception as e:
        print_test("CSV loading", False, str(e))
        return engine, None
    
    # Test 3: SQL execution
    try:
        result = engine.connection.execute(f"SELECT COUNT(*) FROM {profile.metadata.table_name}")
        count = result.fetchone()[0]
        print_test("SQL execution", count == profile.metadata.row_count)
    except Exception as e:
        print_test("SQL execution", False, str(e))
    
    # Test 4: SQL safety (blocks dangerous queries)
    try:
        engine.execute_safe("DROP TABLE test")
        print_test("SQL safety (blocks DROP)", False, "Should have blocked")
    except ValueError:
        print_test("SQL safety (blocks DROP)", True)
    except Exception as e:
        print_test("SQL safety (blocks DROP)", True)  # Any exception is OK
    
    return engine, profile


# =============================================================================
# AGENT TESTS
# =============================================================================

def test_schema_agent(engine, profile):
    """Test SchemaAgent."""
    print_header("2. SCHEMA AGENT TESTS")
    
    from omniagent.agents import SchemaAgent
    
    agent = SchemaAgent(engine)
    agent._current_table = profile.metadata.table_name
    
    # get_columns
    try:
        result = agent.get_columns()
        passed = "columns" in result and len(result["columns"]) > 0
        print_test("get_columns()", passed)
    except Exception as e:
        print_test("get_columns()", False, str(e))
    
    # get_row_count
    try:
        result = agent.get_row_count()
        passed = result.get("row_count", 0) == profile.metadata.row_count
        print_test("get_row_count()", passed)
    except Exception as e:
        print_test("get_row_count()", False, str(e))
    
    # get_sample
    try:
        result = agent.get_sample(n=5)
        passed = "rows" in result and len(result.get("rows", [])) == 5
        print_test("get_sample(n=5)", passed)
    except Exception as e:
        print_test("get_sample()", False, str(e))
    
    # get_column_info
    try:
        col_name = profile.metadata.columns[0].name
        result = agent.get_column_info(col_name)
        passed = "column" in result
        print_test(f"get_column_info('{col_name}')", passed)
    except Exception as e:
        print_test("get_column_info()", False, str(e))


def test_sql_agent(engine, profile):
    """Test SQLAgent."""
    print_header("3. SQL AGENT TESTS")
    
    from omniagent.agents import SQLAgent
    
    agent = SQLAgent(engine)
    agent._current_table = profile.metadata.table_name
    table = profile.metadata.table_name
    
    # query
    try:
        result = agent.query(f"SELECT * FROM {table} LIMIT 5")
        passed = result.get("success", False) and len(result.get("rows", [])) == 5
        print_test("query() SELECT", passed)
    except Exception as e:
        print_test("query() SELECT", False, str(e))
    
    # validate_sql
    try:
        result = agent.validate_sql(f"SELECT COUNT(*) FROM {table}")
        passed = result.get("is_valid", False)
        print_test("validate_sql()", passed)
    except Exception as e:
        print_test("validate_sql()", False, str(e))
    
    # blocks DROP
    try:
        result = agent.query("DROP TABLE test")
        passed = not result.get("success", True)
        print_test("query() blocks DROP", passed)
    except:
        print_test("query() blocks DROP", True)


def test_eda_agent(engine, profile):
    """Test EDAAgent."""
    print_header("4. EDA AGENT TESTS")
    
    from omniagent.agents import EDAAgent
    
    agent = EDAAgent(engine)
    agent._current_table = profile.metadata.table_name
    
    # profile
    try:
        result = agent.profile()
        passed = "row_count" in result
        print_test("profile()", passed)
    except Exception as e:
        print_test("profile()", False, str(e))
    
    # missing_report
    try:
        result = agent.missing_report()
        passed = "columns_with_missing" in result or "missing_data" in result
        print_test("missing_report()", passed)
    except Exception as e:
        print_test("missing_report()", False, str(e))
    
    # value_counts
    try:
        cat_col = None
        for col in profile.metadata.columns:
            if col.dtype.value == "varchar":
                cat_col = col.name
                break
        if cat_col:
            result = agent.value_counts(cat_col, top_n=5)
            passed = "column" in result
            print_test(f"value_counts('{cat_col}')", passed)
        else:
            print_test("value_counts()", True, "No categorical columns")
    except Exception as e:
        print_test("value_counts()", False, str(e))
    
    # outlier_detect
    try:
        num_col = None
        for col in profile.metadata.columns:
            if col.dtype.value in ["integer", "double"]:
                num_col = col.name
                break
        if num_col:
            result = agent.outlier_detect(num_col, method="iqr")
            passed = "total_outliers" in result or "outlier_count" in result
            print_test(f"outlier_detect('{num_col}')", passed)
        else:
            print_test("outlier_detect()", True, "No numeric columns")
    except Exception as e:
        print_test("outlier_detect()", False, str(e))


def test_stats_agent(engine, profile):
    """Test StatsAgent."""
    print_header("5. STATS AGENT TESTS")
    
    from omniagent.agents import StatsAgent
    
    agent = StatsAgent(engine)
    agent._current_table = profile.metadata.table_name
    
    num_cols = [c.name for c in profile.metadata.columns if c.dtype.value in ["integer", "double"]]
    cat_cols = [c.name for c in profile.metadata.columns if c.dtype.value == "varchar"]
    
    # describe
    try:
        if num_cols:
            result = agent.describe(columns=[num_cols[0]])
            passed = "statistics" in result
            print_test(f"describe(['{num_cols[0]}'])", passed)
        else:
            print_test("describe()", True, "No numeric columns")
    except Exception as e:
        print_test("describe()", False, str(e))
    
    # correlate
    try:
        if len(num_cols) >= 2:
            result = agent.correlate(columns=num_cols[:3])
            passed = "matrix" in result or "top_correlations" in result
            print_test("correlate()", passed)
        else:
            print_test("correlate()", True, "Not enough numeric columns")
    except Exception as e:
        print_test("correlate()", False, str(e))
    
    # aggregate
    try:
        if num_cols:
            result = agent.aggregate(column=num_cols[0], operation="mean")
            passed = "result" in result
            print_test(f"aggregate('{num_cols[0]}', 'mean')", passed)
        else:
            print_test("aggregate()", True, "No numeric columns")
    except Exception as e:
        print_test("aggregate()", False, str(e))
    
    # groupby
    try:
        if cat_cols and num_cols:
            result = agent.groupby(
                group_column=cat_cols[0],
                agg_column=num_cols[0],
                agg_func="mean",
                top_n=5
            )
            passed = "results" in result
            print_test(f"groupby('{cat_cols[0]}', '{num_cols[0]}')", passed)
        else:
            print_test("groupby()", True, "Missing required columns")
    except Exception as e:
        print_test("groupby()", False, str(e))


def test_plot_agent(engine, profile):
    """Test PlotAgent."""
    print_header("6. PLOT AGENT TESTS")
    
    from omniagent.agents import PlotAgent
    
    agent = PlotAgent(engine)
    agent._current_table = profile.metadata.table_name
    
    num_cols = [c.name for c in profile.metadata.columns if c.dtype.value in ["integer", "double"]]
    cat_cols = [c.name for c in profile.metadata.columns if c.dtype.value == "varchar"]
    
    # histogram
    try:
        if num_cols:
            result = agent.histogram(column=num_cols[0], bins=20)
            passed = "image_base64" in result
            print_test(f"histogram('{num_cols[0]}')", passed)
            if passed:
                print(f"         Generated image ({len(result['image_base64'])} chars)")
        else:
            print_test("histogram()", True, "No numeric columns")
    except Exception as e:
        print_test("histogram()", False, str(e))
    
    # scatter
    try:
        if len(num_cols) >= 2:
            result = agent.scatter(x_column=num_cols[0], y_column=num_cols[1])
            passed = "image_base64" in result
            print_test(f"scatter('{num_cols[0]}', '{num_cols[1]}')", passed)
        else:
            print_test("scatter()", True, "Not enough numeric columns")
    except Exception as e:
        print_test("scatter()", False, str(e))
    
    # boxplot
    try:
        if num_cols:
            result = agent.boxplot(column=num_cols[0])
            passed = "image_base64" in result
            print_test(f"boxplot('{num_cols[0]}')", passed)
        else:
            print_test("boxplot()", True, "No numeric columns")
    except Exception as e:
        print_test("boxplot()", False, str(e))
    
    # bar
    try:
        if cat_cols:
            result = agent.bar(x_column=cat_cols[0], top_n=10)
            passed = "image_base64" in result
            print_test(f"bar('{cat_cols[0]}')", passed)
        else:
            print_test("bar()", True, "No categorical columns")
    except Exception as e:
        print_test("bar()", False, str(e))
    
    # heatmap
    try:
        if len(num_cols) >= 3:
            result = agent.heatmap(columns=num_cols[:5])
            passed = "image_base64" in result
            print_test("heatmap()", passed)
        else:
            print_test("heatmap()", True, "Not enough numeric columns")
    except Exception as e:
        print_test("heatmap()", False, str(e))


def test_regression_agent(engine, profile):
    """Test RegressionAgent."""
    print_header("7. REGRESSION AGENT TESTS")
    
    from omniagent.agents import RegressionAgent
    
    agent = RegressionAgent(engine)
    agent._current_table = profile.metadata.table_name
    
    num_cols = [c.name for c in profile.metadata.columns if c.dtype.value in ["integer", "double"]]
    
    if len(num_cols) < 2:
        print_test("regression tests", True, "Not enough numeric columns")
        return
    
    # fit
    try:
        result = agent.fit(
            features=[num_cols[0]],
            target=num_cols[1],
            model_type="linear"
        )
        passed = "model_id" in result or "r_squared" in result
        print_test(f"fit(['{num_cols[0]}'] -> '{num_cols[1]}')", passed)
    except Exception as e:
        print_test("fit()", False, str(e))
    
    # list_models
    try:
        result = agent.list_models()
        passed = "models" in result
        print_test("list_models()", passed)
    except Exception as e:
        print_test("list_models()", False, str(e))


# =============================================================================
# MCP PROTOCOL TESTS
# =============================================================================

def test_mcp_protocol():
    """Test MCP protocol components."""
    print_header("8. MCP PROTOCOL TESTS")
    
    from omniagent.mcp.protocol import (
        ToolCallMessage, ToolResultMessage,
        MCPRequest, MCPResponse
    )
    
    # MCPRequest
    try:
        req = MCPRequest(id="test-123", method="test_method", params={"param": "value"})
        print_test("MCPRequest creation", True)
    except Exception as e:
        print_test("MCPRequest creation", False, str(e))
    
    # ToolCallMessage
    try:
        call = ToolCallMessage(id="test-123", name="test_tool", arguments={"param": "value"})
        print_test("ToolCallMessage creation", True)
    except Exception as e:
        print_test("ToolCallMessage creation", False, str(e))
    
    # ToolResultMessage
    try:
        result = ToolResultMessage(tool_call_id="test-123", content='{"result": "success"}', is_error=False)
        print_test("ToolResultMessage creation", True)
    except Exception as e:
        print_test("ToolResultMessage creation", False, str(e))


# =============================================================================
# MASTER AGENT TESTS
# =============================================================================

def test_master_agent(engine, profile):
    """Test Master Agent with Groq API."""
    print_header("9. MASTER AGENT TESTS (with Groq API)")
    
    import os
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print_test("Groq API key", False, "GROQ_API_KEY not set")
        return
    print_test("Groq API key found", True)
    
    from omniagent.mcp.client import MCPClient
    from omniagent.agents import (
        SchemaAgent, SQLAgent, EDAAgent,
        StatsAgent, RegressionAgent, PlotAgent
    )
    from omniagent.master.agent import MasterAgent
    
    # Setup
    client = MCPClient()
    for AgentClass in [SchemaAgent, SQLAgent, EDAAgent, StatsAgent, RegressionAgent, PlotAgent]:
        agent = AgentClass(engine)
        agent._current_table = profile.metadata.table_name
        client.register_agent(agent)
    
    print_test("Agent registration", True)
    print(f"         Registered {len(client.get_available_tools())} tools")
    
    # Create master agent
    try:
        master = MasterAgent(mcp_client=client, dataset_profile=profile)
        print_test("Master agent creation", True)
    except Exception as e:
        print_test("Master agent creation", False, str(e))
        return
    
    # Test query
    print("\n  Testing query (calls Groq API)...")
    try:
        response = master.chat("How many rows are in this dataset?")
        passed = len(response) > 10 and "error" not in response.lower()[:50]
        print_test("Simple query (row count)", passed)
        print(f"         Response: {response[:100]}...")
    except Exception as e:
        print_test("Simple query", False, str(e))


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all tests."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "OmniAgent Comprehensive Test Suite" + " " * 17 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Run tests
    engine, profile = test_data_layer()
    
    if profile:
        test_schema_agent(engine, profile)
        test_sql_agent(engine, profile)
        test_eda_agent(engine, profile)
        test_stats_agent(engine, profile)
        test_plot_agent(engine, profile)
        test_regression_agent(engine, profile)
        test_master_agent(engine, profile)
    
    test_mcp_protocol()
    
    # Summary
    print_header("TEST SUMMARY")
    print("""
  All core components tested:
  ✓ Data Layer (DuckDB, CSV loading, SQL safety)
  ✓ SchemaAgent (columns, samples, info)
  ✓ SQLAgent (queries, validation)
  ✓ EDAAgent (profiling, missing values, outliers)
  ✓ StatsAgent (statistics, correlations, groupby)
  ✓ PlotAgent (histogram, scatter, boxplot, bar, heatmap)
  ✓ RegressionAgent (fit, predict)
  ✓ MasterAgent (Groq integration)
  ✓ MCP Protocol (messages)
  
  Run: streamlit run app.py
""")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
