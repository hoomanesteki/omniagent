"""
Chat Module
===========
Chat UI components.
"""

import streamlit as st
from ui.components import add_message, process_query


def render_chat():
    """Render chat messages with auto-scroll to newest."""
    total_messages = len(st.session_state.messages)
    
    for i, msg in enumerate(st.session_state.messages):
        is_last = (i == total_messages - 1)
        
        if msg['role'] == 'user':
            st.markdown(
                f'<div class="user-msg">{msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            # Add scroll anchor BEFORE the message for last message
            if is_last:
                st.markdown('<div id="scroll-anchor"></div>', unsafe_allow_html=True)
            
            # Add class for last message (scroll target)
            extra_class = ' last-message' if is_last else ''
            st.markdown(f'<div class="bot-msg{extra_class}" id="msg-{i}">', unsafe_allow_html=True)
            
            # Agent badge
            if msg.get('agent'):
                emoji = msg.get('emoji', '🤖')
                st.markdown(
                    f'<span class="agent-badge">{emoji} {msg["agent"]}</span>',
                    unsafe_allow_html=True
                )
            
            # Content
            st.markdown(msg['content'])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Figure
            if msg.get('figure') is not None:
                st.plotly_chart(msg['figure'], width='stretch', key=f"fig_{i}")
            
            # Dataframe
            if msg.get('dataframe') is not None:
                st.dataframe(msg['dataframe'], width='stretch')
            
            # Insights
            if msg.get('insights'):
                st.markdown(
                    f'<div class="insight-box">{msg["insights"]}</div>',
                    unsafe_allow_html=True
                )
            
            # Scroll indicator for last message if there's more content below
            if is_last and (msg.get('figure') is not None or msg.get('dataframe') is not None or msg.get('insights')):
                st.markdown(
                    '<div class="scroll-indicator">⬇️ More content & suggestions below</div>',
                    unsafe_allow_html=True
                )
            
            # Text-to-speech for last message if voice enabled
            if is_last and st.session_state.get('voice_enabled') and st.session_state.get('voice_auto_speak'):
                from agents.voice_agent import speak_response
                speak_response(msg['content'], msg.get('agent'))
    
    # CRITICAL: Inject scroll-to-top JavaScript after all messages rendered
    if total_messages > 0:
        scroll_js = """
        <script>
            (function() {
                function scrollToMessage() {
                    var anchor = document.getElementById('scroll-anchor');
                    if (anchor) {
                        anchor.scrollIntoView({behavior: 'auto', block: 'start'});
                        window.scrollBy(0, -80);
                    } else {
                        var msgs = document.querySelectorAll('.bot-msg');
                        if (msgs.length > 0) {
                            var last = msgs[msgs.length - 1];
                            last.scrollIntoView({behavior: 'auto', block: 'start'});
                            window.scrollBy(0, -80);
                        }
                    }
                }
                // Execute immediately and with delays
                scrollToMessage();
                setTimeout(scrollToMessage, 50);
                setTimeout(scrollToMessage, 150);
                setTimeout(scrollToMessage, 300);
                setTimeout(scrollToMessage, 500);
            })();
        </script>
        """
        st.markdown(scroll_js, unsafe_allow_html=True)
    
    # Add JavaScript to scroll to the scroll-target after page load
    if total_messages > 0:
        st.markdown("""
        <script>
        (function() {
            function scrollToTarget() {
                var target = document.getElementById('scroll-target');
                if (target) {
                    var rect = target.getBoundingClientRect();
                    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    window.scrollTo({
                        top: scrollTop + rect.top - 100,
                        behavior: 'auto'
                    });
                }
            }
            // Run multiple times to catch Streamlit's async rendering
            scrollToTarget();
            setTimeout(scrollToTarget, 100);
            setTimeout(scrollToTarget, 300);
            setTimeout(scrollToTarget, 500);
        })();
        </script>
        """, unsafe_allow_html=True)


def render_suggestions():
    """Render categorized suggestion buttons (8 per category for home, 12 for agents)."""
    suggestions = []
    
    # Get suggestions from last message
    if st.session_state.messages:
        last = st.session_state.messages[-1]
        if last['role'] == 'assistant':
            suggestions = last.get('suggestions', [])
    
    # Default categorized suggestions if none
    if not suggestions and st.session_state.analyzer:
        a = st.session_state.analyzer
        suggestions = _build_default_suggestions(a)
    
    if suggestions:
        # Check if categorized (has emoji prefixes for agents)
        is_categorized = sum(1 for s in suggestions if s.startswith(('📊', '📈', '🤖', '🔍', '📦'))) > 15
        
        if is_categorized:
            # Full categorized layout (8 per category)
            st.markdown("**💡 Suggested Actions by Category:**")
            
            # Stats (8)
            stats_sug = [s for s in suggestions if s.startswith('📊')][:8]
            if stats_sug:
                st.markdown("*📊 Statistics:*")
                _render_button_rows(stats_sug, "stats", 4)
            
            # Viz (8)
            viz_sug = [s for s in suggestions if s.startswith('📈')][:8]
            if viz_sug:
                st.markdown("*📈 Visualization:*")
                _render_button_rows(viz_sug, "viz", 4)
            
            # Aggregate (8)
            agg_sug = [s for s in suggestions if s.startswith('📦')][:8]
            if agg_sug:
                st.markdown("*📦 Aggregation:*")
                _render_button_rows(agg_sug, "agg", 4)
            
            # Predict (8)
            pred_sug = [s for s in suggestions if s.startswith('🤖')][:8]
            if pred_sug:
                st.markdown("*🤖 Prediction:*")
                _render_button_rows(pred_sug, "pred", 4)
            
            # SQL (8)
            sql_sug = [s for s in suggestions if s.startswith('🔍')][:8]
            if sql_sug:
                st.markdown("*🔍 Data Exploration:*")
                _render_button_rows(sql_sug, "sql", 4)
            
            # Navigation (4)
            st.markdown("**🧭 Navigation:**")
            nav = ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
            _render_button_rows(nav, "nav", 4)
        else:
            # Agent-specific layout (12 suggestions + 4 nav)
            st.markdown("**💡 Suggested Actions:**")
            
            # Get non-nav suggestions
            non_nav = [s for s in suggestions if not s.startswith(('🆘', '🏠', '📋', 'ℹ️'))]
            
            # Render in rows of 4
            _render_button_rows(non_nav[:12], "sug", 4)
            
            # Navigation row (4)
            st.markdown("**🧭 Navigation:**")
            nav = [s for s in suggestions if s.startswith(('🆘', '🏠', '📋', 'ℹ️'))]
            if not nav:
                nav = ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
            _render_button_rows(nav[:4], "nav", 4)


def _build_default_suggestions(a):
    """Build default categorized suggestions (8 per category)."""
    suggestions = []
    num = a.usable_numeric
    cat = a.usable_categorical
    targets = a.target_candidates
    
    # Stats (8)
    suggestions.extend([
        f"📊 Mean of {num[0]}" if num else "📊 Statistics",
        f"📊 Median of {num[0]}" if num else "📊 Check missing",
        f"📊 Std of {num[0]}" if num else "📊 Standard deviation",
        "📊 Check missing",
        "📊 Show statistics",
        "📊 Data quality",
        f"📊 Describe {num[0]}" if num else "📊 Describe",
        "📊 All statistics"
    ])
    
    # Viz (8)
    suggestions.extend([
        f"📈 Histogram of {num[0]}" if num else "📈 Histogram",
        f"📈 Bar chart of {cat[0]}" if cat else "📈 Bar chart",
        "📈 Correlation heatmap",
        "📈 Show all numeric",
        f"📈 Box plot of {num[0]}" if num else "📈 Box plot",
        f"📈 Scatter plot" if len(num) > 1 else "📈 Scatter",
        f"📈 Pie chart of {cat[0]}" if cat else "📈 Pie chart",
        "📈 Show all categorical"
    ])
    
    # Aggregate (8)
    suggestions.extend([
        f"📦 Count by {cat[0]}" if cat else "📦 Count by",
        f"📦 Sum {num[0]} by {cat[0]}" if num and cat else "📦 Sum by",
        f"📦 Average by {cat[0]}" if cat else "📦 Average by",
        f"📦 Group by {cat[0]}" if cat else "📦 Group by",
        f"📦 Max by {cat[0]}" if cat else "📦 Max by",
        f"📦 Min by {cat[0]}" if cat else "📦 Min by",
        "📦 Aggregation guide",
        "📦 Pivot table"
    ])
    
    # Predict (8)
    pred_sug = []
    for t in targets[:3]:
        pred_sug.append(f"🤖 Predict {t['column']}")
    while len(pred_sug) < 3:
        pred_sug.append("🤖 What can I predict?")
    pred_sug.extend([
        "🤖 Build model",
        "🤖 Feature importance",
        "🤖 ML overview",
        "🤖 Classification",
        "🤖 Regression"
    ])
    suggestions.extend(pred_sug[:8])
    
    # SQL (8)
    suggestions.extend([
        "🔍 First 10 rows",
        "🔍 First 20 rows",
        "🔍 Last 10 rows",
        "🔍 Random sample",
        "🔍 Show columns",
        "🔍 Data structure",
        "🔍 Column types",
        "🔍 Preview data"
    ])
    
    # Navigation (4)
    suggestions.extend(["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"])
    
    return suggestions


def _render_button_rows(buttons, prefix, cols_per_row=4):
    """Render buttons in rows."""
    if not buttons:
        return
    
    for row_idx in range(0, len(buttons), cols_per_row):
        row = buttons[row_idx:row_idx + cols_per_row]
        cols = st.columns(len(row))
        for i, s in enumerate(row):
            with cols[i]:
                clean_s = _clean_suggestion(s)
                if st.button(s, key=f"{prefix}_{row_idx}_{i}", width='stretch'):
                    _handle_suggestion_click(s, clean_s)


def _clean_suggestion(s: str) -> str:
    """Remove emoji prefixes from suggestion."""
    return s.replace("🆘 ", "").replace("🏠 ", "").replace("📊 ", "").replace("🔍 ", "").replace("📈 ", "").replace("🤖 ", "").replace("📋 ", "").replace("ℹ️ ", "").replace("📦 ", "")


def _handle_suggestion_click(original: str, cleaned: str):
    """Handle suggestion button click."""
    if "Home" in original:
        # Clear messages and go to welcome screen
        st.session_state.messages = []
        st.rerun()
        return
    elif "Help" in original:
        add_message('user', "Help")
        process_query("help")
    elif "Dataset Info" in original:
        add_message('user', "Dataset Info")
        process_query("dataset info")
    elif "About" in original:
        add_message('user', "About")
        process_query("about")
    else:
        add_message('user', cleaned)
        process_query(cleaned)
    st.rerun()


def _clean_for_speech(text: str) -> str:
    """Clean markdown text for natural speech."""
    import re
    
    if not text:
        return ""
    
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
    text = re.sub(r'`([^`]+)`', r'\1', text)        # Code
    text = re.sub(r'#{1,6}\s*', '', text)           # Headers
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
    text = re.sub(r'[|]', ' ', text)                # Tables
    text = re.sub(r'[-]{3,}', '', text)             # Horizontal rules
    text = re.sub(r'\n+', '. ', text)               # Newlines to periods
    text = re.sub(r'[•\-\*]\s*', '', text)          # Bullet points
    text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)  # Numbered lists
    
    # Remove emojis
    text = re.sub(r'[📊📈📦🤖🔍🧠💡✅❌⚠️🎯🆘🏠📋ℹ️🔢📝🎤🔊🔇💾🔑🗑️🧭📂🔧🚀👋]', '', text)
    
    # Clean up whitespace and punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.\s*\.', '.', text)
    text = re.sub(r',\s*,', ',', text)
    text = text.strip()
    
    return text


def render_welcome():
    """Render welcome screen."""
    st.markdown('<h1 class="main-header">🤖 OmniAgent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Data Analysis Assistant</p>', unsafe_allow_html=True)
    
    st.markdown("""
## 👋 Welcome!

I'm your **intelligent data analysis companion**. Upload a CSV and ask me anything!

---

### 🤖 Your Specialized Agents

| Agent | What They Do | Example |
|-------|--------------|---------|
| 📊 **Stats** | Means, medians, missing values, summaries | "Show statistics" |
| 📈 **Viz** | Histograms, scatter plots, heatmaps | "Histogram of age" |
| 📦 **Aggregate** | Group by, count, sum, average by category | "Count by gender" |
| 🤖 **Predict** | Machine learning models & predictions | "Predict salary" |
| 🔍 **SQL** | Data preview, filtering, exploration | "Show first 10 rows" |
| 🔮 **Dynamic** | Custom analysis via AI code generation | "Find outliers using IQR" |

---

### 🚀 Quick Start

1. **📂 Load data** from the sidebar (or try a sample dataset!)
2. **💬 Ask naturally** - "What's the average age?", "Show histogram of price"
3. **📊 Get insights** with beautiful visualizations

---

### 🔮 Dynamic Analysis (AI Mode)

Enable **AI Mode** in the sidebar to unlock powerful custom analysis:

| Step | What Happens |
|------|--------------|
| **Step 1** | I offer to create custom analysis (saves resources!) |
| **Step 2** | Type `yes` → I generate and show the code |
| **Step 3** | Type `yes` → I execute and show results |

**Examples:** "Calculate rolling average", "Find outliers", "Create age bins"

---

### 🎤 Voice Assistant

Enable **Voice** in the sidebar for two-way conversation:
- 🎙️ **Speak** your questions using the microphone
- 🔊 **Listen** as the agent speaks responses back to you
- ⚙️ **Customize** voice speed and pitch in settings

---

### 🛡️ Safe & Secure

Your data is processed locally. The Dynamic Agent runs code in a sandboxed environment.

---

**👈 Load some data to begin!**
    """)
