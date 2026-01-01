"""
Core Configuration Module
=========================
Centralized configuration for OmniAgent.

Made with ❤️ by Hooman Esteki
https://esteki.ca/
"""

import os
from pathlib import Path
from typing import List

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Application configuration."""
    
    # Author
    AUTHOR = "Hooman Esteki"
    AUTHOR_URL = "https://esteki.ca/"
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    SAMPLES_DIR = DATA_DIR / "samples"
    UPLOADS_DIR = DATA_DIR / "uploads"
    
    # LLM Settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_MAX_TOKENS = 2000
    LLM_TEMPERATURE = 0.1
    LLM_TIMEOUT = 30
    
    # UI Settings
    PAGE_TITLE = "🤖 OmniAgent"
    PAGE_ICON = "🤖"
    LAYOUT = "wide"
    
    # Chart Colors
    COLORS: List[str] = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c', 
        '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
    ]
    
    # Agent Settings
    MAX_SUGGESTIONS = 12
    MAX_CHART_COLUMNS = 12
    MAX_TABLE_ROWS = 50
    
    # Sample Datasets
    SAMPLE_DATASETS = {
        "🏋️ Fitness": "fitness_tracker.csv",
        "🏠 Airbnb": "nyc_airbnb.csv",
        "🛒 Sales": "ecommerce_sales.csv"
    }
    
    @classmethod
    def get_sample_path(cls, name: str) -> Path:
        """Get path to sample dataset."""
        filename = cls.SAMPLE_DATASETS.get(name)
        if filename:
            return cls.SAMPLES_DIR / filename
        return None


# CSS Styles
STYLES = """
<style>
    .main-header {
        font-size: 2.5rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        text-align: center;
    }
    .sub-header {
        text-align: center; 
        color: #666; 
        margin-bottom: 1.5rem;
    }
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white; 
        padding: 15px 20px;
        border-radius: 20px 20px 5px 20px; 
        margin: 12px 0; 
        max-width: 70%; 
        margin-left: auto; 
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .bot-msg {
        background: linear-gradient(135deg, #f8f9fa 0%, #fff 100%); 
        color: #1f1f1f; 
        padding: 20px 25px;
        border-radius: 20px 20px 20px 5px; 
        margin: 12px 0; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); 
        line-height: 1.8; 
        border: 1px solid #e8e8e8;
    }
    .agent-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white;
        padding: 6px 14px; 
        border-radius: 20px; 
        display: inline-block; 
        font-weight: 600; 
        font-size: 0.85rem; 
        margin-bottom: 12px;
    }
    .insight-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
        border-left: 5px solid #4caf50;
        padding: 18px 22px; 
        border-radius: 0 12px 12px 0; 
        margin: 18px 0; 
        line-height: 1.7; 
        color: #1a1a1a !important;
    }
    .insight-box * {
        color: #1a1a1a !important;
    }
    .stButton > button {
        border-radius: 25px !important; 
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important; 
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4) !important;
    }
    .scroll-indicator {
        text-align: center;
        padding: 10px;
        color: #667eea;
        font-size: 0.9rem;
        animation: bounce 2s infinite;
    }
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-5px); }
        60% { transform: translateY(-3px); }
    }
    .last-message {
        scroll-margin-top: 20px;
    }
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
</style>
<script>
    // CRITICAL: Scroll to TOP of last bot message
    (function() {
        function scrollToTop() {
            var msgs = document.querySelectorAll('.bot-msg');
            if (msgs.length > 0) {
                var lastMsg = msgs[msgs.length - 1];
                var rect = lastMsg.getBoundingClientRect();
                var scrollY = window.pageYOffset || document.documentElement.scrollTop;
                var targetY = scrollY + rect.top - 100;
                window.scrollTo(0, Math.max(0, targetY));
            }
        }
        // Run multiple times to catch Streamlit renders
        scrollToTop();
        setTimeout(scrollToTop, 100);
        setTimeout(scrollToTop, 250);
        setTimeout(scrollToTop, 500);
    })();
</script>
"""
