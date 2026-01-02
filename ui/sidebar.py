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
        st.caption("AI-Powered Data Analysis")
        st.divider()
        
        # AI Settings Section
        _render_ai_settings()
        
        st.divider()
        
        # Voice Settings Section
        _render_voice_settings()
        
        st.divider()
        
        # Data Loading Section
        _render_data_loading()
        
        st.divider()
        
        # Current Data Info
        _render_data_info()
        
        st.divider()
        
        # Navigation
        _render_navigation()


def _render_voice_settings():
    """Render voice control settings."""
    from agents.voice_agent import render_voice_controls
    render_voice_controls()


def _render_ai_settings():
    """Render AI settings section with validation."""
    st.markdown("### 🧠 AI Assistant")
    
    # AI toggle
    ai_enabled = st.toggle(
        "Enable AI Mode",
        value=st.session_state.get('ai_enabled', False),
        key="ai_toggle"
    )
    st.session_state.ai_enabled = ai_enabled
    
    if not ai_enabled:
        st.caption("Enable for smarter responses")
        return
    
    # Check if API key exists and is validated
    api_key = st.session_state.get('api_key', '')
    llm = st.session_state.get('llm')
    is_valid = llm and llm.available
    
    if not api_key or not is_valid:
        st.warning("⚠️ API Key Required")
        
        st.markdown("""
**Get Free Groq API Key:**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free, no credit card)
3. Go to API Keys → Create
4. Copy & paste below
        """)
        
        new_key = st.text_input(
            "Groq API Key:",
            value=api_key,
            type="password",
            placeholder="gsk_xxxxxxxxxxxx",
            key="groq_key_input"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Validate", key="validate_ai_key", width='stretch'):
                if new_key:
                    if new_key.startswith("gsk_"):
                        with st.spinner("Validating..."):
                            # Test the key
                            test_llm = LLMClient(new_key)
                        
                        if test_llm.available:
                            st.session_state.api_key = new_key
                            st.session_state.llm = test_llm
                            if st.session_state.get('master'):
                                st.session_state.master.llm = test_llm
                            st.success("✅ AI Enabled!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid key or connection error")
                    else:
                        st.error("❌ Key should start with 'gsk_'")
                else:
                    st.error("Please enter an API key")
        
        with col2:
            st.link_button("🔗 Get Key", "https://console.groq.com", width='stretch')
        
        st.info("💡 App works without AI, but with basic responses")
    
    else:
        # AI is active
        st.success("✅ AI Active")
        st.caption(f"Model: {llm.model}")
        
        # Update LLM state
        if llm:
            llm.toggle(ai_enabled)
        
        # Settings
        with st.expander("⚙️ Settings"):
            st.caption(f"**API Key:** {api_key[:10]}...{api_key[-4:]}")
            
            if st.button("🔄 Change API Key", key="change_ai_key"):
                st.session_state.api_key = ''
                st.session_state.llm = LLMClient('')
                st.rerun()
            
            if st.button("🧪 Test AI", key="test_ai"):
                with st.spinner("Testing..."):
                    try:
                        response = llm.understand_query("test", "testing connection")
                        if response:
                            st.success("✅ AI is responding!")
                        else:
                            st.warning("⚠️ AI may be slow")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)[:50]}")


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
        if st.button(name, width='stretch', key=f"s_{name}"):
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
            if st.button("📊 Numeric", width='stretch', key="num_btn"):
                add_message('user', "Show all numeric")
                process_query("show all numeric")
                st.rerun()
        with col2:
            if st.button("📝 Categorical", width='stretch', key="cat_btn"):
                add_message('user', "Show all categorical")
                process_query("show all categorical")
                st.rerun()


def _render_navigation():
    """Render navigation section."""
    st.markdown("### 🧭 Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆘 Help", width='stretch'):
            add_message('user', "Help")
            process_query("help")
            st.rerun()
    with col2:
        if st.button("🏠 Home", width='stretch'):
            add_message('user', "🏠 Home")
            process_query("tell me about this dataset")
            st.rerun()
    
    if st.button("🗑️ Clear Chat", width='stretch'):
        st.session_state.messages = []
        st.rerun()
    
    # Footer
    st.divider()
    st.markdown(
        f"<div style='text-align: center; color: #888; font-size: 12px;'>"
        f"Made with ❤️ by <a href='{Config.AUTHOR_URL}' target='_blank' style='color: #888;'>{Config.AUTHOR}</a>"
        f"</div>",
        unsafe_allow_html=True
    )
