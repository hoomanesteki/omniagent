# OmniAgent Security Guide
## Security Best Practices and Considerations

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication](#authentication)
3. [API Key Management](#api-key-management)
4. [Data Security](#data-security)
5. [Input Validation](#input-validation)
6. [Dependency Security](#dependency-security)
7. [Deployment Security](#deployment-security)
8. [Security Checklist](#security-checklist)

---

## Security Overview

OmniAgent processes potentially sensitive data and connects to external APIs. This document outlines security best practices.

### Security Layers

```
┌─────────────────────────────────────┐
│         Application Layer           │
│    Input Validation, Sanitization   │
├─────────────────────────────────────┤
│           API Layer                 │
│    Key Management, Rate Limiting    │
├─────────────────────────────────────┤
│           Data Layer                │
│   Encryption, Access Control        │
├─────────────────────────────────────┤
│        Infrastructure Layer         │
│    Network, Container Security      │
└─────────────────────────────────────┘
```

---

## Authentication

### Current State

OmniAgent is designed as a single-user local application. For production deployment with multiple users, implement:

### Recommended Authentication

```python
# Example: Streamlit authentication
import streamlit_authenticator as stauth

# Define users
credentials = {
    "usernames": {
        "admin": {
            "name": "Admin User",
            "password": "$hashed_password_here"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "omniagent_cookie",
    "secret_key",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login()

if authentication_status:
    # User is authenticated
    main_app()
elif authentication_status == False:
    st.error("Username/password is incorrect")
```

### Session Security

```python
# Secure session configuration
import secrets

def init_secure_session():
    """Initialize secure session with CSRF protection."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = secrets.token_urlsafe(32)
    if 'csrf_token' not in st.session_state:
        st.session_state.csrf_token = secrets.token_urlsafe(32)
```

---

## API Key Management

### Environment Variables

```bash
# .env file (NEVER commit to git)
GROQ_API_KEY=gsk_your_key_here

# .gitignore (ensure .env is listed)
.env
*.env
.env.*
```

### Key Storage Best Practices

```python
# ✅ Good: Load from environment
import os
api_key = os.getenv("GROQ_API_KEY")

# ❌ Bad: Hardcoded key
api_key = "gsk_abc123..."  # NEVER do this
```

### Key Rotation

```python
def rotate_api_key(new_key: str):
    """Rotate API key with validation."""
    # Validate new key format
    if not new_key.startswith('gsk_'):
        raise ValueError("Invalid key format")
    
    # Test new key
    test_client = LLMClient(new_key)
    if not test_client.is_active():
        raise ValueError("New key is invalid")
    
    # Update environment
    os.environ["GROQ_API_KEY"] = new_key
    
    # Reload client
    st.session_state.llm = LLMClient(new_key)
```

### Secrets Management for Production

```python
# AWS Secrets Manager
import boto3

def get_secret(secret_name: str) -> str:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Azure Key Vault
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_azure_secret(vault_url: str, secret_name: str) -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    return client.get_secret(secret_name).value
```

---

## Data Security

### Data Classification

| Level | Description | Examples |
|-------|-------------|----------|
| Public | Non-sensitive | Sample datasets |
| Internal | Business data | Sales reports |
| Confidential | Sensitive | Customer PII |
| Restricted | Highly sensitive | Financial data |

### Data Handling

```python
# Sanitize uploaded data
def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove potentially sensitive columns."""
    sensitive_patterns = [
        'ssn', 'social_security', 'password', 'credit_card',
        'card_number', 'cvv', 'pin', 'secret'
    ]
    
    columns_to_drop = []
    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in sensitive_patterns):
            columns_to_drop.append(col)
    
    if columns_to_drop:
        logger.warning(f"Dropping sensitive columns: {columns_to_drop}")
        df = df.drop(columns=columns_to_drop)
    
    return df
```

### Data Masking

```python
def mask_pii(df: pd.DataFrame) -> pd.DataFrame:
    """Mask PII data in DataFrame."""
    df = df.copy()
    
    # Email masking
    if 'email' in df.columns:
        df['email'] = df['email'].apply(
            lambda x: x[:3] + '***@***' + x.split('@')[-1][-4:] if pd.notna(x) else x
        )
    
    # Phone masking
    if 'phone' in df.columns:
        df['phone'] = df['phone'].apply(
            lambda x: '***-***-' + str(x)[-4:] if pd.notna(x) else x
        )
    
    return df
```

### Memory Security

```python
# Clear sensitive data from memory
import gc

def secure_cleanup():
    """Securely clear sensitive data."""
    if 'df' in st.session_state:
        del st.session_state.df
    if 'api_key' in st.session_state:
        st.session_state.api_key = None
    gc.collect()
```

---

## Input Validation

### Query Sanitization

```python
import re
import html

def sanitize_query(query: str) -> str:
    """Sanitize user query input."""
    if not query:
        return ""
    
    # Remove HTML
    query = html.escape(query)
    
    # Remove potential SQL injection
    query = re.sub(r'[;\'"\\]', '', query)
    
    # Limit length
    query = query[:1000]
    
    # Remove control characters
    query = ''.join(char for char in query if char.isprintable() or char.isspace())
    
    return query.strip()
```

### File Upload Validation

```python
import magic

ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def validate_upload(uploaded_file) -> bool:
    """Validate uploaded file."""
    # Check extension
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {ext} not allowed")
    
    # Check size
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValueError(f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")
    
    # Check MIME type
    mime = magic.from_buffer(uploaded_file.read(1024), mime=True)
    uploaded_file.seek(0)
    
    allowed_mimes = {
        'text/csv', 'application/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    if mime not in allowed_mimes:
        raise ValueError(f"Invalid file type: {mime}")
    
    return True
```

### Column Name Validation

```python
def validate_column_name(col: str, df: pd.DataFrame) -> str:
    """Safely resolve column name."""
    # Direct match
    if col in df.columns:
        return col
    
    # Case-insensitive match
    col_lower = col.lower()
    for c in df.columns:
        if c.lower() == col_lower:
            return c
    
    # No match - don't expose column names in error
    raise ValueError("Column not found")
```

---

## Dependency Security

### Requirements Pinning

```txt
# requirements.txt - Pin exact versions
streamlit==1.28.0
pandas==2.0.3
numpy==1.24.3
plotly==5.17.0
scikit-learn==1.3.0
python-dotenv==1.0.0
requests==2.31.0
```

### Security Scanning

```bash
# Install safety
pip install safety

# Check for vulnerabilities
safety check -r requirements.txt

# Or use pip-audit
pip install pip-audit
pip-audit
```

### Dependency Update Policy

1. **Monthly**: Check for security updates
2. **Immediately**: Patch critical vulnerabilities
3. **Quarterly**: Update to latest minor versions
4. **Annually**: Consider major version upgrades

---

## Deployment Security

### Docker Security

```dockerfile
# Dockerfile with security best practices
FROM python:3.11-slim

# Don't run as root
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements first (caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Don't store secrets in image
ENV GROQ_API_KEY=""

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

### Network Security

```yaml
# docker-compose.yml with network isolation
version: '3.8'
services:
  omniagent:
    build: .
    ports:
      - "8501:8501"
    networks:
      - frontend
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    read_only: true
    security_opt:
      - no-new-privileges:true

networks:
  frontend:
    driver: bridge
```

### HTTPS Configuration

```python
# Streamlit config for HTTPS (.streamlit/config.toml)
[server]
enableCORS = false
enableXsrfProtection = true

# For production, use reverse proxy (nginx)
```

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name omniagent.example.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Security Checklist

### Development

- [ ] No hardcoded secrets
- [ ] .env in .gitignore
- [ ] Input validation on all user inputs
- [ ] Dependencies pinned and scanned
- [ ] Error messages don't expose internals

### Deployment

- [ ] HTTPS enabled
- [ ] Non-root container user
- [ ] Environment variables for secrets
- [ ] Rate limiting configured
- [ ] Logging enabled (without PII)

### Operations

- [ ] API keys rotated regularly
- [ ] Dependencies updated monthly
- [ ] Security scans in CI/CD
- [ ] Backup and recovery tested
- [ ] Incident response plan documented

---

## Incident Response

### If API Key is Compromised

1. **Immediately**: Revoke key in Groq console
2. Generate new key
3. Update environment variables
4. Restart application
5. Review access logs
6. Document incident

### If Data Breach Suspected

1. **Immediately**: Take service offline
2. Preserve logs and evidence
3. Identify scope of breach
4. Notify affected parties
5. Remediate vulnerability
6. Document and review

---

## Security Contacts

For security issues, contact:
- **Author**: Hooman Esteki
- **Website**: https://esteki.ca/

---

*Last updated: 2026-01-01*
