"""
Sidebar Module
==============
Sidebar UI components.
"""

import streamlit as st
from pathlib import Path

from core.config import Config
from core.llm import LLMClient
from ui.components import load_data, add_message, get_loaded_message, process_query


def render_sidebar():
    """Render the sidebar UI."""
    with st.sidebar:
        st.markdown("## 🤖 OmniAgent")
        st.caption("AI Data Analysis")
        st.markdown(f"Made with ❤️ by [{Config.AUTHOR}]({Config.AUTHOR_URL})", unsafe_allow_html=True)
        st.divider()
        
        # AI Settings Section
        _render_ai_settings()
        
        st.divider()
        
        # Data Loading Section
        _render_data_loading()
        
        st.divider()
        
        # Current Data Info
        _render_data_info()
        
        st.divider()
        
        # Navigation
        _render_navigation()


def _render_ai_settings():
    """Render AI settings section."""
    st.markdown("### 🧠 AI Settings")
    
    if st.session_state.llm and st.session_state.llm.available:
        # AI is available - show toggle
        ai_enabled = st.toggle(
            "Enable AI Mode",
            value=st.session_state.ai_enabled,
            key="ai_toggle"
        )
        st.session_state.ai_enabled = ai_enabled
        
        if st.session_state.llm:
            st.session_state.llm.toggle(ai_enabled)
        
        if ai_enabled:
            st.success("🧠 AI Mode: **Active**")
            st.caption(f"Model: {st.session_state.llm.model}")
        else:
            st.warning("💡 AI Mode: **Disabled**")
            st.caption("Using keyword matching only")
    else:
        # AI is offline - show help and setup
        st.error("⚠️ **AI Offline**")
        st.caption("App works but AI features disabled")
        
        # Help button to show setup guide in chat
        if st.button("❓ How to Enable AI", use_container_width=True, key="ai_help_btn"):
            _show_ai_setup_guide()
            st.rerun()
        
        st.markdown("---")
        st.markdown("**🔑 Quick Setup:**")
        
        # API Key input directly visible
        api_key = st.text_input(
            "Paste your Groq API Key:",
            type="password",
            placeholder="gsk_xxxxxxxxxxxx",
            key="api_input",
            help="Get free key at console.groq.com"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save", use_container_width=True, key="save_key"):
                if api_key and api_key.startswith("gsk_"):
                    st.session_state.api_key = api_key
                    st.session_state.llm = LLMClient(api_key)
                    if st.session_state.master:
                        st.session_state.master.llm = st.session_state.llm
                    st.success("✅ Saved!")
                    st.rerun()
                elif api_key:
                    st.error("Key should start with 'gsk_'")
        with col2:
            st.link_button("🔗 Get Key", "https://console.groq.com", use_container_width=True)


def _show_ai_setup_guide():
    """Show AI setup guide in chat."""
    guide_content = """## 🔧 How to Enable AI Features

OmniAgent uses **Groq's free AI API** to provide smarter, more natural responses. Here's how to set it up:

### 📝 Step-by-Step Guide

**Step 1: Create a Groq Account**
- Go to [console.groq.com](https://console.groq.com)
- Sign up with Google or email (it's free!)

**Step 2: Generate API Key**
- Once logged in, go to "API Keys"
- Click "Create API Key"
- Give it a name (e.g., "OmniAgent")
- Copy the key (starts with `gsk_`)

**Step 3: Add Key to OmniAgent**
- Paste your key in the sidebar under "AI Settings"
- Click "Save"
- You should see "AI Mode: Active" ✅

### 💡 What AI Mode Adds

| Feature | Without AI | With AI |
|---------|------------|---------|
| Query Understanding | Keywords only | Natural language |
| Response Quality | Basic | Detailed & contextual |
| Unknown Queries | Error message | AI tries to help |
| Insights | Template-based | AI-generated |

### 🆓 Is it Free?

Yes! Groq offers a generous free tier:
- No credit card required
- Thousands of requests per day
- Fast responses (Groq is very fast!)

### 🔒 Is it Safe?

- Your API key stays in your browser
- Data is processed by Groq (not stored)
- You can delete the key anytime

---

**👈 Add your API key in the sidebar to get started!**"""
    
    add_message('assistant', guide_content, agent="System", emoji="⚙️")


def _render_data_loading():
    """Render data loading section."""
    st.markdown("### 📂 Load Data")
    
    # File uploader
    uploaded = st.file_uploader(
        "Upload CSV",
        type=['csv'],
        label_visibility="collapsed"
    )
    
    if uploaded and st.session_state.filename != uploaded.name:
        if load_data(uploaded, uploaded.name):
            add_message('user', f"📂 Load {uploaded.name}")
            msg = get_loaded_message()
            add_message(
                'assistant',
                msg['content'],
                insights=msg['insights'],
                suggestions=msg['suggestions'],
                agent="Master Agent",
                emoji="🧠"
            )
            st.rerun()
    
    # Sample datasets
    st.markdown("**Sample Datasets:**")
    for name, filename in Config.SAMPLE_DATASETS.items():
        path = Config.SAMPLES_DIR / filename
        if st.button(name, use_container_width=True, key=f"s_{name}"):
            if path.exists() and load_data(path):
                add_message('user', f"📂 {name}")
                msg = get_loaded_message()
                add_message(
                    'assistant',
                    msg['content'],
                    insights=msg['insights'],
                    suggestions=msg['suggestions'],
                    agent="Master Agent",
                    emoji="🧠"
                )
                st.rerun()


def _render_data_info():
    """Render current data info section."""
    if st.session_state.df is not None:
        st.markdown("### 📊 Current Data")
        st.markdown(f"**{st.session_state.filename}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rows", f"{len(st.session_state.df):,}")
        with col2:
            st.metric("Cols", len(st.session_state.df.columns))
        
        # Quick chart buttons
        st.markdown("**Quick Charts:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Numeric", use_container_width=True, key="num_btn"):
                add_message('user', "Show all numeric")
                process_query("show all numeric")
                st.rerun()
        with col2:
            if st.button("📝 Categorical", use_container_width=True, key="cat_btn"):
                add_message('user', "Show all categorical")
                process_query("show all categorical")
                st.rerun()


def _render_navigation():
    """Render navigation section."""
    st.markdown("### 🧭 Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆘 Help", use_container_width=True):
            add_message('user', "Help")
            process_query("help")
            st.rerun()
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            add_message('user', "🏠 Home")
            process_query("tell me about this dataset")
            st.rerun()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
