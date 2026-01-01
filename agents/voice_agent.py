"""
Voice Agent Module - Two-Way Conversation
==========================================
Complete voice interaction system:
- Speech-to-Text: Browser API (you speak)
- Text-to-Speech: Browser API (agent responds)
- Two-way natural conversation
- Optional ElevenLabs for premium voice

Made with ❤️ by Hooman Esteki
https://esteki.ca/
"""

import streamlit as st
import streamlit.components.v1 as components
import re
from typing import Optional


class VoiceAgent:
    """Voice Agent for two-way conversation."""
    
    name = "Voice Agent"
    emoji = "🎤"
    
    def __init__(self):
        self._init_session()
    
    def _init_session(self):
        """Initialize session state."""
        defaults = {
            'voice_enabled': False,
            'voice_auto_speak': True,
            'voice_rate': 1.0,
            'voice_pitch': 1.0,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
    
    def clean_text(self, text: str) -> str:
        """Clean text for natural speech."""
        if not text:
            return ""
        
        # Remove markdown
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'[|]', ' ', text)
        text = re.sub(r'[-]{3,}', '', text)
        
        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        # Clean whitespace
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\.\s*\.', '.', text)
        
        return text.strip()


def render_voice_controls():
    """Render voice controls in sidebar."""
    st.markdown("### 🎤 Voice Assistant")
    
    # Main toggle
    voice_enabled = st.toggle(
        "Enable Voice",
        value=st.session_state.get('voice_enabled', False),
        key="voice_toggle_main"
    )
    st.session_state.voice_enabled = voice_enabled
    
    if not voice_enabled:
        st.caption("Enable for two-way voice conversation")
        return
    
    st.success("✅ Voice Active")
    st.caption("Speak your questions, hear responses!")
    
    # Auto-speak toggle
    auto = st.checkbox(
        "🔊 Auto-speak responses",
        value=st.session_state.get('voice_auto_speak', True),
        key="voice_auto_speak_check"
    )
    st.session_state.voice_auto_speak = auto
    
    # Voice settings
    with st.expander("⚙️ Voice Settings"):
        rate = st.slider(
            "Speaking Speed",
            min_value=0.5,
            max_value=2.0,
            value=st.session_state.get('voice_rate', 1.0),
            step=0.1,
            key="voice_rate_slider"
        )
        st.session_state.voice_rate = rate
        
        pitch = st.slider(
            "Voice Pitch",
            min_value=0.5,
            max_value=2.0,
            value=st.session_state.get('voice_pitch', 1.0),
            step=0.1,
            key="voice_pitch_slider"
        )
        st.session_state.voice_pitch = pitch
        
        # Test voice
        if st.button("🔊 Test Voice", key="test_voice_btn"):
            test_script = _get_tts_script(
                "Hello! I'm your AI data assistant. Ask me anything about your data and I'll help you analyze it!",
                rate, pitch
            )
            st.markdown(test_script, unsafe_allow_html=True)
            st.info("🔊 Speaking...")
    
    st.divider()
    
    # Voice Input Section
    st.markdown("**🎙️ Speak to Me:**")
    _render_voice_input()


def _render_voice_input():
    """Render voice input component with auto-submit."""
    
    rate = st.session_state.get('voice_rate', 1.0)
    pitch = st.session_state.get('voice_pitch', 1.0)
    
    voice_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                background: transparent;
            }}
            .container {{ padding: 8px; }}
            .status {{
                padding: 14px;
                background: #1e1e2e;
                border: 2px solid #444;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 12px;
                font-size: 14px;
                color: #fff;
                min-height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .status.listening {{ 
                border-color: #4CAF50; 
                background: linear-gradient(135deg, #1a2e1a 0%, #1e3a1e 100%);
                animation: pulse 1.5s infinite;
            }}
            .status.success {{ border-color: #4CAF50; }}
            .status.error {{ border-color: #f44336; background: #2e1a1a; }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}
            .btn {{
                width: 100%;
                padding: 16px;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin: 6px 0;
                transition: all 0.2s;
            }}
            .btn:hover {{ transform: scale(1.02); }}
            .btn:active {{ transform: scale(0.98); }}
            .btn-speak {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }}
            .btn-stop {{
                background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                color: white;
                padding: 12px;
                font-size: 14px;
            }}
            .note {{
                font-size: 12px;
                color: #888;
                margin-top: 10px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div id="status" class="status">🎤 Click button and speak your question</div>
            
            <button class="btn btn-speak" onclick="startListening()">
                🎤 Start Speaking
            </button>
            
            <button class="btn btn-stop" onclick="stopAll()">
                🔇 Stop All Audio
            </button>
            
            <p class="note">💡 Speaks directly to chat - like a real conversation!</p>
        </div>
        
        <script>
            let recognition = null;
            const VOICE_RATE = {rate};
            const VOICE_PITCH = {pitch};
            
            function startListening() {{
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                
                if (!SpeechRecognition) {{
                    showStatus('⚠️ Please use Chrome or Edge browser', 'error');
                    return;
                }}
                
                // Stop any ongoing speech
                if (window.parent.speechSynthesis) {{
                    window.parent.speechSynthesis.cancel();
                }}
                
                if (recognition) {{
                    try {{ recognition.stop(); }} catch(e) {{}}
                }}
                
                recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = true;
                recognition.lang = 'en-US';
                
                showStatus('🔴 Listening... speak now!', 'listening');
                
                recognition.onresult = function(event) {{
                    let final = '';
                    let interim = '';
                    
                    for (let i = event.resultIndex; i < event.results.length; i++) {{
                        const t = event.results[i][0].transcript;
                        if (event.results[i].isFinal) {{
                            final += t;
                        }} else {{
                            interim += t;
                        }}
                    }}
                    
                    if (final) {{
                        showStatus('✅ Sending: "' + final + '"', 'success');
                        sendToChat(final);
                    }} else if (interim) {{
                        showStatus('🎤 ' + interim + '...', 'listening');
                    }}
                }};
                
                recognition.onerror = function(event) {{
                    if (event.error === 'not-allowed') {{
                        showStatus('❌ Microphone blocked! Click 🔒 in address bar → Allow', 'error');
                    }} else if (event.error === 'no-speech') {{
                        showStatus('❌ No speech heard. Try again!', 'error');
                    }} else if (event.error === 'aborted') {{
                        showStatus('🎤 Click button to speak', '');
                    }} else {{
                        showStatus('❌ Error: ' + event.error, 'error');
                    }}
                }};
                
                recognition.onend = function() {{
                    const s = document.getElementById('status');
                    if (s && s.classList.contains('listening')) {{
                        showStatus('🎤 Click button and speak your question', '');
                    }}
                }};
                
                try {{
                    recognition.start();
                }} catch(e) {{
                    if (e.name === 'InvalidStateError') {{
                        recognition.stop();
                        setTimeout(() => recognition.start(), 100);
                    }} else {{
                        showStatus('❌ ' + e.message, 'error');
                    }}
                }}
            }}
            
            function stopAll() {{
                // Stop recognition
                if (recognition) {{
                    try {{ recognition.stop(); }} catch(e) {{}}
                    recognition = null;
                }}
                
                // Stop speech in parent window
                if (window.parent.speechSynthesis) {{
                    window.parent.speechSynthesis.cancel();
                }}
                
                // Stop speech in this window
                if (window.speechSynthesis) {{
                    window.speechSynthesis.cancel();
                }}
                
                showStatus('🎤 Click button and speak your question', '');
            }}
            
            function showStatus(text, type) {{
                const s = document.getElementById('status');
                s.innerHTML = text;
                s.className = 'status' + (type ? ' ' + type : '');
            }}
            
            function sendToChat(text) {{
                try {{
                    const parent = window.parent.document;
                    
                    // Find all textareas
                    const textareas = parent.querySelectorAll('textarea');
                    let chatInput = null;
                    
                    // Find the chat input
                    for (let ta of textareas) {{
                        const placeholder = (ta.placeholder || '').toLowerCase();
                        if (placeholder.includes('ask') || placeholder.includes('message') || placeholder.includes('anything')) {{
                            chatInput = ta;
                            break;
                        }}
                    }}
                    
                    // Fallback to last textarea
                    if (!chatInput && textareas.length > 0) {{
                        chatInput = textareas[textareas.length - 1];
                    }}
                    
                    if (chatInput) {{
                        // Set value using native setter (React compatible)
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        nativeSetter.call(chatInput, text);
                        
                        // Trigger events
                        chatInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        chatInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        chatInput.focus();
                        
                        // Auto-submit after delay
                        setTimeout(function() {{
                            // Method 1: Find form submit button
                            const form = chatInput.closest('form');
                            if (form) {{
                                const btns = form.querySelectorAll('button');
                                for (let btn of btns) {{
                                    if (btn.type === 'submit' || btn.getAttribute('kind') === 'primary') {{
                                        btn.click();
                                        showStatus('✅ Sent! Waiting for response...', 'success');
                                        return;
                                    }}
                                }}
                            }}
                            
                            // Method 2: Press Enter key
                            chatInput.dispatchEvent(new KeyboardEvent('keydown', {{
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            }}));
                            
                            showStatus('✅ Sent!', 'success');
                        }}, 300);
                        
                    }} else {{
                        showStatus('⚠️ Could not find chat input', 'error');
                    }}
                }} catch(e) {{
                    showStatus('❌ Error: ' + e.message, 'error');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    components.html(voice_html, height=230)


def _get_tts_script(text: str, rate: float = 1.0, pitch: float = 1.0) -> str:
    """Generate browser TTS JavaScript."""
    agent = VoiceAgent()
    clean = agent.clean_text(text)
    
    if not clean or len(clean) < 2:
        return ""
    
    # Limit length for speech
    if len(clean) > 600:
        clean = clean[:600] + ". See screen for more."
    
    # Escape for JS
    clean = (clean
        .replace('\\', '\\\\')
        .replace("'", "\\'")
        .replace('"', '\\"')
        .replace('\n', ' ')
        .replace('\r', '')
    )
    
    return f"""
    <script>
    (function() {{
        if ('speechSynthesis' in window) {{
            // Cancel any ongoing speech
            window.speechSynthesis.cancel();
            
            // Create utterance
            const utterance = new SpeechSynthesisUtterance("{clean}");
            utterance.rate = {rate};
            utterance.pitch = {pitch};
            utterance.volume = 1.0;
            utterance.lang = 'en-US';
            
            // Try to get a good voice
            function speak() {{
                const voices = window.speechSynthesis.getVoices();
                if (voices.length > 0) {{
                    // Prefer Google or high-quality voices
                    const goodVoice = voices.find(v => 
                        v.lang.startsWith('en') && 
                        (v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Daniel'))
                    ) || voices.find(v => v.lang.startsWith('en-US')) 
                      || voices.find(v => v.lang.startsWith('en'));
                    
                    if (goodVoice) {{
                        utterance.voice = goodVoice;
                    }}
                }}
                window.speechSynthesis.speak(utterance);
            }}
            
            // Voices might not be loaded yet
            if (window.speechSynthesis.getVoices().length > 0) {{
                setTimeout(speak, 100);
            }} else {{
                window.speechSynthesis.onvoiceschanged = speak;
            }}
        }}
    }})();
    </script>
    """


def speak_response(text: str, agent_name: str = None):
    """Speak response if voice is enabled - this creates two-way conversation."""
    if not st.session_state.get('voice_enabled', False):
        return
    
    if not st.session_state.get('voice_auto_speak', True):
        return
    
    agent = VoiceAgent()
    
    # Add conversational intro based on agent
    intros = {
        'Stats Agent': "Here's what I found. ",
        'Viz Agent': "I've created a chart for you. ",
        'Prediction Agent': "Here are the prediction results. ",
        'Aggregate Agent': "Here's the aggregated data. ",
        'SQL Agent': "Here's your data. ",
        'Master Agent': "",
    }
    
    intro = ""
    if agent_name and agent_name in intros:
        intro = intros[agent_name]
    
    full_text = intro + text
    
    # Generate TTS
    rate = st.session_state.get('voice_rate', 1.0)
    pitch = st.session_state.get('voice_pitch', 1.0)
    
    tts_script = _get_tts_script(full_text, rate, pitch)
    if tts_script:
        st.markdown(tts_script, unsafe_allow_html=True)


# Global instance
voice_agent = VoiceAgent()
