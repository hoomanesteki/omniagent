"""
🤖 OmniAgent - AI Data Analysis Assistant
==========================================

A modular, multi-agent data analysis system with MCP communication.

Run: streamlit run app.py
"""

import streamlit as st

from ui import (
    init_page,
    init_session,
    add_message,
    process_query,
    render_sidebar,
    render_chat,
    render_suggestions,
    render_welcome
)


def main():
    """Main application entry point."""
    # Initialize
    init_page()
    init_session()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    if not st.session_state.messages:
        render_welcome()
    else:
        st.markdown('<h1 class="main-header">🤖 OmniAgent</h1>', unsafe_allow_html=True)
        render_chat()
    
    # Divider before suggestions
    st.divider()
    
    # Suggestions (only if data loaded)
    if st.session_state.df is not None:
        render_suggestions()
    
    # Chat input
    user_input = st.chat_input(
        "Ask anything... (e.g., 'mean of price', 'histogram of age', 'predict sales')"
    )
    
    if user_input:
        add_message('user', user_input)
        process_query(user_input)
        st.rerun()


if __name__ == "__main__":
    main()
