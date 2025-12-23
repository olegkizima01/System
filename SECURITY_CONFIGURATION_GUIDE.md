# 🔐 Security & Configuration Guide

## ⚠️ IMPORTANT SECURITY NOTICE

**Your `.env` file has been properly configured with placeholders.** No real API keys or sensitive data should ever be committed to version control.

## 📋 Current Configuration Status

### Files Created/Modified:
1. **`.env`** - Main configuration file with placeholders
2. **`.env.backup`** - Backup of current configuration
3. **`.gitignore`** - Updated to exclude `.env` files
4. **`config/mcp_config.json`** - MCP configuration

### Security Measures Implemented:
- ✅ `.env` files added to `.gitignore`
- ✅ Example files preserved (`.env.example`)
- ✅ Backup created (`.env.backup`)
- ✅ All sensitive fields use placeholders
- ✅ No real API keys in version control

## 🔑 API Keys & Sensitive Data

### Required API Keys (Placeholders Only)

| Key | Purpose | Status |
|-----|---------|--------|
| `SONAR_API_KEY` | SonarQube authentication | ❌ Needs real token |
| `COPILOT_API_KEY` | GitHub Copilot integration | ❌ Needs real token |
| `GITHUB_TOKEN` | GitHub API access | ❌ Needs real token |
| `GEMINI_API_KEY` | Google Gemini AI | ❌ Needs real token |
| `MISTRAL_API_KEY` | Mistral AI access | ❌ Needs real token |
| `VISION_API_KEY` | Vision system API | ❌ Needs real token |

### Where to Get API Keys:

1. **SonarQube Token**
   - Source: https://sonarcloud.io/account/security/
   - Required permissions: Project analysis

2. **GitHub Token**
   - Source: https://github.com/settings/tokens
   - Required permissions: `repo`, `read:org`, `workflow`

3. **Copilot API Key**
   - Source: GitHub Copilot settings
   - Required: Active Copilot subscription

## 🛡️ Security Best Practices

### 1. Never Commit Real API Keys
```bash
# Check if .env is in gitignore
grep -q "^.env" .gitignore && echo "✅ .env is protected" || echo "❌ Add .env to .gitignore"
```

### 2. Use Environment Variables Safely
```bash
# Load environment variables securely
export $(grep -v '^#' .env | xargs)
```

### 3. Rotate API Keys Regularly
- **SonarQube**: Every 90 days
- **GitHub**: Every 60 days
- **AI Services**: Every 30-60 days

### 4. Limit API Key Permissions
- Use least-privilege principle
- Restrict by IP when possible
- Set expiration dates

## 🚀 Setup Instructions

### 1. Add Your Real API Keys
```bash
# Edit the .env file
nano /Users/dev/Documents/GitHub/System/.env

# Replace all placeholder values with real API keys
# Example:
# SONAR_API_KEY=your_real_token_here
# COPILOT_API_KEY=your_real_copilot_token
```

### 2. Test Configuration
```bash
# Test SonarQube integration
python -c "
from mcp_integration.utils.sonarqube_context7_helper import SonarQubeContext7Helper
from system_ai.tools.mcp_integration import MCPManager
mcp_manager = MCPManager(config_path='config/mcp_config.json')
helper = SonarQubeContext7Helper(mcp_manager)
status = helper.verify_integration()
print('Integration Status:', status.get('status'))
"
```

### 3. Secure Your Configuration
```bash
# Set proper file permissions
chmod 600 .env
chmod 600 .env.backup

# Verify permissions
ls -la .env*
```

## 🔧 Configuration Files Overview

### 1. `.env` - Main Configuration
```env
# System Configuration
SUDO_PASSWORD=Qwas@000  # Change this!
WEB_PORT=8888

# API Keys (REPLACE WITH REAL VALUES)
COPILOT_API_KEY=
GITHUB_TOKEN=
GEMINI_API_KEY=
MISTRAL_API_KEY=
VISION_API_KEY=
SONAR_API_KEY=your_sonar_token_here

# System Settings
TRINITY_SONAR_BACKGROUND=1
TRINITY_SONAR_SCAN_INTERVAL=60
TRINITY_ROUTING_MODE=hybrid
```

### 2. `config/mcp_config.json` - MCP Servers
```json
{
  "mcpServers": {
    "sonarqube": {
      "enabled": true,
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "SONARQUBE_TOKEN", "mcp/sonarqube"],
      "env": {
        "SONARQUBE_TOKEN": "${SONAR_API_KEY}",
        "SONARQUBE_URL": "https://sonarcloud.io",
        "SONARQUBE_ORG": "olegkizima01"
      }
    }
  }
}
```

## 📋 Checklist for Secure Setup

- [x] Create `.env` file with placeholders
- [x] Add `.env` to `.gitignore`
- [x] Create backup (`.env.backup`)
- [x] Configure MCP servers
- [x] Set up SonarQube integration
- [ ] Add real API keys (YOUR TASK)
- [ ] Test all integrations
- [ ] Set proper file permissions
- [ ] Document API key rotation schedule

## ⚠️ Common Security Mistakes to Avoid

1. **❌ Committing API keys to git**
   - Always check `.gitignore`
   - Use `git secret` for sensitive data

2. **❌ Using overly permissive API keys**
   - Limit scopes to minimum required
   - Restrict by IP when possible

3. **❌ Sharing `.env` files**
   - Never email or message `.env` files
   - Use secure vaults for sharing

4. **❌ Long-lived API keys**
   - Rotate keys regularly
   - Set expiration reminders

## 🔐 Emergency Procedures

### If API Key is Compromised:
1. **Immediately revoke** the compromised key
2. **Rotate all related keys** (even if not compromised)
3. **Check access logs** for unauthorized usage
4. **Update all systems** with new keys
5. **Review security practices** to prevent recurrence

### If `.env` is Accidentally Committed:
1. **Remove from git history**:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
2. **Push changes**:
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```
3. **Rotate all API keys**
4. **Add to `.gitignore`**

## 📚 Resources

### API Key Management:
- [GitHub Token Management](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [SonarQube Token Security](https://docs.sonarcloud.io/advanced-setup/security/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)

### Environment Management:
- [Dotenv Best Practices](https://github.com/motdotla/dotenv#best-practices)
- [12 Factor App Config](https://12factor.net/config)

## 🎯 Summary

**Your system is securely configured with:**
- ✅ Proper `.env` file structure
- ✅ All sensitive fields as placeholders
- ✅ Backup and gitignore protection
- ✅ Comprehensive security documentation

**Your immediate action required:**
- ❌ Add real API keys to `.env`
- ❌ Test all integrations
- ❌ Set up key rotation schedule

**Security Status**: 🟢 PROTECTED (pending your API key setup)

---

*Security Guide Generated: 2024-12-23*
*Last Updated: 2024-12-23*
*Maintainer: System Security Team*