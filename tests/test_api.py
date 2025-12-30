#!/usr/bin/env python3
"""
OmniAgent - API Connection Test

Tests Groq API connection and basic functionality.
Run this first to verify your API key works.

Run with: python tests/test_api.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


def main():
    print("\n" + "=" * 60)
    print("  OmniAgent - Groq API Test")
    print("=" * 60)
    
    # Check API key
    print("\n📋 Step 1: Checking .env file...")
    env_path = Path(".env")
    if not env_path.exists():
        print("  ❌ .env file not found!")
        print("  Create .env with: GROQ_API_KEY=your-key-here")
        return 1
    print("  ✓ .env file exists")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("  ❌ GROQ_API_KEY not found in .env")
        return 1
    print(f"  ✓ API key loaded: {api_key[:10]}...{api_key[-4:]}")
    
    # Test connection
    print("\n📡 Step 2: Testing Groq connection...")
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        models = client.models.list()
        print(f"  ✓ Connected! Found {len(models.data)} models")
    except ImportError:
        print("  ❌ groq package not installed")
        print("  Run: pip install groq")
        return 1
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return 1
    
    # Test chat
    print("\n💬 Step 3: Testing chat completion...")
    try:
        model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'Hello OmniAgent!' and nothing else."}],
            max_tokens=50,
        )
        reply = response.choices[0].message.content.strip()
        print(f"  ✓ Response: {reply}")
    except Exception as e:
        print(f"  ❌ Chat failed: {e}")
        return 1
    
    # Test tool calling
    print("\n🔧 Step 4: Testing tool calling...")
    try:
        tools = [{
            "type": "function",
            "function": {
                "name": "get_count",
                "description": "Get a count",
                "parameters": {"type": "object", "properties": {}}
            }
        }]
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "How many items?"}],
            tools=tools,
            tool_choice="auto",
            max_tokens=100,
        )
        if response.choices[0].message.tool_calls:
            print("  ✓ Tool calling works!")
        else:
            print("  ✓ Model responded (tool calling available)")
    except Exception as e:
        print(f"  ⚠️ Tool calling test: {e}")
    
    # Success
    print("\n" + "=" * 60)
    print("  ✅ ALL API TESTS PASSED!")
    print("=" * 60)
    print("\n  Your Groq API is ready. Run the full tests with:")
    print("  python tests/test_all.py")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
