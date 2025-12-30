"""
OmniAgent - AI-Powered Data Analyst

A Streamlit application for conversational data analysis.
Features:
- CSV file upload and analysis
- Natural language queries
- Visualizations with proper image rendering
- Guided exploration

Run with: streamlit run app.py
"""

import streamlit as st
from pathlib import Path
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="OmniAgent - AI Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "messages": [],
        "dataset_loaded": False,
        "dataset_profile": None,
        "master_agent": None,
        "db_engine": None,
        "current_file": None,
        "images": {},  # Store images by message index
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def setup_agents():
    """Initialize the agent system."""
    from omniagent.data.duckdb_engine import DuckDBEngine
    from omniagent.mcp.client import MCPClient
    from omniagent.agents import (
        SchemaAgent, SQLAgent, EDAAgent,
        StatsAgent, RegressionAgent, PlotAgent,
    )
    from omniagent.master.agent import MasterAgent
    
    if st.session_state.db_engine is None:
        st.session_state.db_engine = DuckDBEngine()
    
    db = st.session_state.db_engine
    
    client = MCPClient()
    client.register_agent(SchemaAgent(db))
    client.register_agent(SQLAgent(db))
    client.register_agent(EDAAgent(db))
    client.register_agent(StatsAgent(db))
    client.register_agent(RegressionAgent(db))
    client.register_agent(PlotAgent(db))
    
    master = MasterAgent(
        mcp_client=client,
        dataset_profile=st.session_state.dataset_profile,
    )
    st.session_state.master_agent = master
    
    return master


def load_dataset(uploaded_file):
    """Load an uploaded CSV file."""
    from omniagent.data.loader import DataLoader
    
    if st.session_state.db_engine is None:
        from omniagent.data.duckdb_engine import DuckDBEngine
        st.session_state.db_engine = DuckDBEngine()
    
    loader = DataLoader(db_engine=st.session_state.db_engine)
    profile = loader.load_file(uploaded_file, uploaded_file.name)
    
    st.session_state.dataset_profile = profile
    st.session_state.dataset_loaded = True
    
    # Reset agents
    st.session_state.master_agent = None
    setup_agents()
    
    return profile


def get_suggestions() -> list[str]:
    """Get question suggestions based on dataset."""
    profile = st.session_state.dataset_profile
    if not profile:
        return []
    
    meta = profile.metadata
    num_cols = [c.name for c in meta.columns if c.dtype.value in ['integer', 'double']]
    cat_cols = [c.name for c in meta.columns if c.dtype.value == 'varchar']
    
    suggestions = [
        "📊 Show descriptive statistics",
        "🔍 Check for missing values",
    ]
    
    if num_cols:
        suggestions.append(f"📈 Create histogram of {num_cols[0]}")
    if cat_cols:
        suggestions.append(f"📉 Show bar chart of {cat_cols[0]}")
    if len(num_cols) >= 2:
        suggestions.append("🔗 Show correlation heatmap")
    
    return suggestions[:4]


def handle_error(error_msg: str) -> str:
    """Convert errors to user-friendly messages."""
    error_lower = error_msg.lower()
    
    if "429" in error_msg or "rate_limit" in error_lower:
        return """⚠️ **Rate Limit Reached**

Please wait a moment and try again, or ask a simpler question."""
    
    elif "413" in error_msg or "too large" in error_lower:
        return """⚠️ **Request Too Large**

Try asking about one column at a time."""
    
    elif "tool_use_failed" in error_lower or "tool call validation" in error_lower:
        return """⚠️ **Tool Error**

The AI had trouble with that request. Please try rephrasing your question.

**Try these instead:**
- "Show statistics for [column_name]"
- "Create a bar chart of [column_name]"
- "How many rows are there?"
"""
    
    else:
        return f"❌ Error: {error_msg[:200]}"


def render_sidebar():
    """Render the sidebar."""
    with st.sidebar:
        st.title("📊 OmniAgent")
        st.markdown("*AI-Powered Data Analyst*")
        st.divider()
        
        # File upload
        st.subheader("📁 Upload Dataset")
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            help="Upload a CSV file to analyze",
        )
        
        if uploaded_file is not None:
            if not st.session_state.dataset_loaded or \
               st.session_state.current_file != uploaded_file.name:
                with st.spinner("Loading..."):
                    try:
                        profile = load_dataset(uploaded_file)
                        st.session_state.current_file = uploaded_file.name
                        st.success(f"✅ Loaded {profile.metadata.row_count:,} rows!")
                        
                        welcome = f"""Great! I've loaded **{uploaded_file.name}** with {profile.metadata.row_count:,} rows and {profile.metadata.column_count} columns.

I can help you:
- 📊 Summarize and explore your data
- 🔍 Find patterns and correlations
- 📈 Create visualizations
- 🤖 Answer questions in plain English

**What would you like to know?**"""
                        st.session_state.messages = [{"role": "assistant", "content": welcome}]
                        st.session_state.images = {}
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Dataset info
        if st.session_state.dataset_loaded and st.session_state.dataset_profile:
            st.divider()
            st.subheader("📋 Dataset Info")
            
            meta = st.session_state.dataset_profile.metadata
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rows", f"{meta.row_count:,}")
            with col2:
                st.metric("Columns", meta.column_count)
            
            with st.expander("View Columns"):
                for col in meta.columns:
                    icon = {"integer": "🔢", "double": "🔢", "varchar": "📝"}.get(col.dtype.value, "📊")
                    st.text(f"{icon} {col.name}")
            
            # Quick actions that work reliably
            st.divider()
            st.subheader("⚡ Quick Actions")
            
            num_cols = [c.name for c in meta.columns if c.dtype.value in ['integer', 'double']]
            cat_cols = [c.name for c in meta.columns if c.dtype.value == 'varchar']
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Statistics", use_container_width=True):
                    st.session_state.pending_message = "Show descriptive statistics for all numeric columns"
                    st.rerun()
            with col2:
                if st.button("🔍 Missing", use_container_width=True):
                    st.session_state.pending_message = "Are there any missing values in the dataset?"
                    st.rerun()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📈 Histogram", use_container_width=True):
                    if num_cols:
                        st.session_state.pending_message = f"Create a histogram of {num_cols[0]}"
                    else:
                        st.session_state.pending_message = "Show a chart"
                    st.rerun()
            with col2:
                if st.button("📉 Bar Chart", use_container_width=True):
                    if cat_cols:
                        st.session_state.pending_message = f"Create a bar chart showing counts for {cat_cols[0]}"
                    else:
                        st.session_state.pending_message = "Show a bar chart"
                    st.rerun()
            
            if len(num_cols) >= 2:
                if st.button("🔗 Correlation Heatmap", use_container_width=True):
                    st.session_state.pending_message = "Show a correlation heatmap for all numeric columns"
                    st.rerun()
        
        # Clear chat
        st.divider()
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.images = {}
            if st.session_state.master_agent:
                st.session_state.master_agent.reset_conversation()
            st.rerun()
        
        # Model info
        st.divider()
        model = os.getenv('LLM_MODEL', 'llama-3.1-8b-instant')
        st.caption(f"Model: {model}")
        st.caption("💡 Tip: Use 'llama-3.3-70b-versatile' for better results")


def render_suggestions():
    """Render suggestion buttons."""
    suggestions = get_suggestions()
    if not suggestions:
        return
    
    st.markdown("**💡 Try asking:**")
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            clean = suggestion.lstrip("📊🔍📈📉📋🔗❓💡🤖🎯 ")
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_message = clean
                st.rerun()


def display_message_with_images(message: dict, msg_idx: int):
    """Display a message and any associated images."""
    st.markdown(message["content"])
    
    # Check for images stored for this message
    if msg_idx in st.session_state.images:
        for img_b64 in st.session_state.images[msg_idx]:
            try:
                img_bytes = base64.b64decode(img_b64)
                st.image(img_bytes, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not display image: {e}")


def extract_images_from_response(response: str) -> tuple[str, list[str]]:
    """Extract any base64 images from the response."""
    images = []
    
    # Check if response contains image data (from tool results)
    # This is a simplified check - in practice, images come from the master agent
    
    return response, images


def render_chat():
    """Render the main chat interface."""
    st.title("💬 Chat with your Data")
    
    if not st.session_state.dataset_loaded:
        st.markdown("""
### 👋 Welcome to OmniAgent!

I'm your AI data analysis assistant. Upload a CSV file to get started.

**What I can do:**
- 📊 Summarize your data with statistics
- 🔍 Find patterns and correlations
- 📈 Create visualizations
- 🤖 Answer questions about your data
        """)
        
        # Sample datasets
        st.divider()
        st.subheader("📂 Or try a sample dataset:")
        
        samples_dir = Path("data/samples")
        if samples_dir.exists():
            sample_files = list(samples_dir.glob("*.csv"))
            if sample_files:
                cols = st.columns(min(len(sample_files), 3))
                for i, sample_path in enumerate(sample_files[:3]):
                    with cols[i]:
                        if st.button(f"📁 {sample_path.stem}", key=f"sample_{i}", use_container_width=True):
                            import io
                            with open(sample_path, "rb") as f:
                                file_obj = io.BytesIO(f.read())
                                file_obj.name = sample_path.name
                                load_dataset(file_obj)
                                st.session_state.current_file = sample_path.name
                            st.rerun()
        return
    
    # Display messages with images
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            display_message_with_images(message, idx)
    
    # Show suggestions
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        st.divider()
        render_suggestions()
    
    # Handle input
    if "pending_message" in st.session_state and st.session_state.pending_message:
        prompt = st.session_state.pending_message
        st.session_state.pending_message = None
    else:
        prompt = st.chat_input("Ask me anything about your data...")
    
    if prompt:
        # Add user message
        msg_idx = len(st.session_state.messages)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing..."):
                try:
                    if st.session_state.master_agent is None:
                        setup_agents()
                    
                    # Get response and images
                    response, images = st.session_state.master_agent.chat_with_images(prompt)
                    
                    # Display response
                    st.markdown(response)
                    
                    # Display and store images
                    if images:
                        st.session_state.images[msg_idx + 1] = images
                        for img_b64 in images:
                            try:
                                img_bytes = base64.b64decode(img_b64)
                                st.image(img_bytes, use_container_width=True)
                            except:
                                pass
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_response = handle_error(str(e))
                    st.markdown(error_response)
                    st.session_state.messages.append({"role": "assistant", "content": error_response})
        
        st.rerun()


def main():
    """Main application entry point."""
    init_session_state()
    
    if st.session_state.db_engine is None:
        from omniagent.data.duckdb_engine import DuckDBEngine
        st.session_state.db_engine = DuckDBEngine()
    
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
