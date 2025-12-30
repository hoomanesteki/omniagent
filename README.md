# 🤖 OmniAgent v2 - AI Data Analysis Assistant

A Streamlit application for interactive data analysis with optional LLM support.

## ✨ Features

- **Works with OR without API key!**
  - With API key: Natural language understanding via Groq LLM
  - Without API key: Smart keyword matching (still very capable!)
- **6 Types of Visualizations**: Histogram, Scatter, Bar, Box, Heatmap, Pie
- **Statistical Analysis**: Describe, Correlation, Outliers, Missing values
- **ML Predictions**: Linear, Random Forest, Gradient Boosting
- **3 Sample Datasets**: Fitness, Airbnb, E-commerce

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Option A: Conda (recommended)
conda env create -f environment.yml
conda activate omniagent

# Option B: Pip
pip install -r requirements.txt
pip install python-dotenv  # For .env file support
```

### 2. Configure (Optional but Recommended)

```bash
# Copy example .env file
cp .env.example .env

# Edit .env and add your Groq API key
# Get free key at: https://console.groq.com
```

### 3. Run Tests

```bash
python tests/test_all.py
```

### 4. Start the App

```bash
streamlit run app_with_llm.py
```

## 📁 Project Structure

```
omniagent/
├── app_with_llm.py          # Main app (with LLM support)
├── app.py                   # Simple version (no LLM)
├── requirements.txt         # Pip dependencies
├── environment.yml          # Conda environment
├── .env.example             # Environment template
├── README.md                # This file
├── data/
│   └── samples/
│       ├── fitness_tracker.csv
│       ├── nyc_airbnb.csv
│       └── ecommerce_sales.csv
└── tests/
    └── test_all.py          # Comprehensive tests
```

## 🔑 Environment Variables (.env file)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| GROQ_API_KEY | No | None | Your Groq API key |
| LLM_MODEL | No | llama-3.3-70b-versatile | Model to use |

Example `.env` file:
```
GROQ_API_KEY=gsk_your_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

## 💬 Example Queries

**Statistics:**
- Show descriptive statistics
- Check for missing values
- Find outliers in price

**Visualizations:**
- Show histogram of age
- Create correlation heatmap
- Bar chart of category
- Scatter plot of price vs quantity

**Predictions:**
- Predict price using other columns
- Train model for target

## 🤖 Agent System

| Agent | Purpose |
|-------|---------|
| 📋 Schema Agent | Data structure & info |
| 📊 Stats Agent | Statistics, correlation, outliers |
| 📈 Plot Agent | All visualizations |
| 🔮 Prediction Agent | ML models |
| 🎯 Master Agent | Orchestrates everything |

## ⚠️ Rate Limits

Groq free tier has limits (30 requests/minute). If you hit rate limits:
- Wait a moment and retry
- The app automatically falls back to keyword matching
- Consider upgrading your Groq plan

## 🧪 Testing

Run all tests:
```bash
python tests/test_all.py
```

This tests:
- Sample datasets loading
- All agent functions
- Keyword matching
- Edge cases
- File structure
- Python syntax

## 📝 License

MIT
