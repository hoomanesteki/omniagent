"""
Pytest Configuration and Shared Fixtures
=========================================
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def fitness_df():
    """Create a fitness tracker-like dataframe."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'user_id': range(1, n + 1),
        'age': np.random.randint(18, 65, n),
        'gender': np.random.choice(['Male', 'Female'], n),
        'activity_type': np.random.choice(['Running', 'Cycling', 'Swimming', 'Walking'], n),
        'duration_minutes': np.random.randint(15, 120, n),
        'calories_burned': np.random.randint(100, 800, n),
        'heart_rate_avg': np.random.randint(80, 180, n),
        'steps': np.random.randint(1000, 20000, n),
        'workout_intensity': np.random.choice(['Low', 'Medium', 'High'], n),
    })


@pytest.fixture
def ecommerce_df():
    """Create an e-commerce-like dataframe."""
    np.random.seed(42)
    n = 150
    return pd.DataFrame({
        'order_id': range(1001, 1001 + n),
        'customer_id': np.random.randint(1, 50, n),
        'product': np.random.choice(['Laptop', 'Phone', 'Tablet', 'Watch', 'Headphones'], n),
        'category': np.random.choice(['Electronics', 'Accessories'], n),
        'price': np.random.uniform(50, 2000, n).round(2),
        'quantity': np.random.randint(1, 5, n),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n),
        'payment_method': np.random.choice(['Credit Card', 'PayPal', 'Debit Card'], n),
    })


@pytest.fixture
def simple_df():
    """Create a simple dataframe for basic tests."""
    return pd.DataFrame({
        'numeric1': [1, 2, 3, 4, 5],
        'numeric2': [10, 20, 30, 40, 50],
        'category1': ['A', 'B', 'A', 'B', 'A'],
        'category2': ['X', 'Y', 'X', 'Y', 'X'],
    })


@pytest.fixture
def df_with_missing():
    """Create a dataframe with missing values."""
    return pd.DataFrame({
        'complete': [1, 2, 3, 4, 5],
        'some_missing': [1, None, 3, None, 5],
        'all_missing': [None, None, None, None, None],
        'category': ['A', 'B', None, 'A', 'B'],
    })


@pytest.fixture
def large_df():
    """Create a larger dataframe for performance tests."""
    np.random.seed(42)
    n = 10000
    return pd.DataFrame({
        'id': range(n),
        'value1': np.random.randn(n),
        'value2': np.random.randn(n),
        'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], n),
    })


# Mock streamlit session state
@pytest.fixture(autouse=True)
def mock_streamlit_session():
    """Mock streamlit session state for tests."""
    import streamlit as st
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    yield
    # Clean up
    if hasattr(st, 'session_state'):
        st.session_state.clear()
