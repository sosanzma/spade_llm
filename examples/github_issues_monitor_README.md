# GitHub Issues/PRs Monitor with Email Notification System

A comprehensive 4-agent SPADE_LLM example demonstrating:
- **Input Guardrails**: GitHub-only request filtering
- **GitHub MCP Integration**: Repository analysis and monitoring  
- **Notion MCP with HTTP Streaming**: Structured data storage
- **Human-in-the-Loop (HITL)**: Email confirmation workflow
- **Gmail MCP**: Professional email notifications

## 🏗️ Architecture

```
User Request → ChatAgent (Guardrails) → GitHubAnalyzer → NotionManager → EmailManager ← Human Expert
                   ↓                        ↓               ↓               ↓
              GitHub Filter            GitHub MCP      Notion MCP     Gmail MCP + HITL
```

### Agent Responsibilities

1. **ChatAgent**: Entry point with GitHub keyword guardrails
2. **GitHubAnalyzerAgent**: Repository analysis using GitHub MCP
3. **NotionManagerAgent**: Data storage using Notion MCP HTTP streaming
4. **EmailManagerAgent**: Human-confirmed email notifications via Gmail MCP

## 🔧 Prerequisites

### Required Services
- **XMPP Server**: For agent communication
- **OpenAI API Key**: For LLM processing
- **GitHub Personal Access Token**: For repository access
- **Notion Integration**: Customer ID for Notion MCP
- **Gmail Access**: For email sending capabilities

### Development Setup
```bash
# Install SPADE_LLM framework
pip install -e .

# Start human expert web interface (in separate terminal)
python -m spade_llm.human_interface.web_server

# Ensure Node.js is available for MCP servers
npm --version
```

## ⚙️ Configuration

### 1. Environment Variables
Create a `.env` file or set environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export GITHUB_TOKEN="your-github-personal-access-token"
```

### 2. Notion MCP Configuration
Update the Notion MCP URL in the example with your customer ID:
```python
notion_mcp = StreamableHttpServerConfig(
    name="NotionMCP",
    url="https://mcp.composio.dev/partner/composio/notion/mcp?customerId=YOUR-CUSTOMER-ID",
    # ... rest of config
)
```

### 3. XMPP Server
Ensure your XMPP server is running and supports WebSocket connections for the human interface.

## 🚀 Running the Example

### 1. Start the Human Expert Interface
```bash
# Terminal 1: Start web interface for human expert
python -m spade_llm.human_interface.web_server

# Open http://localhost:8080 in your browser
```

### 2. Run the Main Example
```bash
# Terminal 2: Run the GitHub monitor
python examples/github_issues_monitor_example.py
```

### 3. Follow the Setup Prompts
- Enter OpenAI API key (if not in environment)
- Enter GitHub token (if not in environment)  
- Enter XMPP server domain
- Enter passwords for all agent accounts
- Enter user interface password

## 📋 Usage Examples

### Basic Repository Analysis
```
🐙 GitHub> Analyze issues and pull requests for the main repository
```

### Specific Repository  
```
🐙 GitHub> Review recent activity in microsoft/vscode repository
```

### Current Project Status
```
🐙 GitHub> Check the status of issues and PRs for our project
```

## 🔄 Workflow Details

### 1. Input Processing (ChatAgent)
- **Guardrails**: Only GitHub-related requests pass through
- **Blocked requests**: "I only help with GitHub-related requests..."
- **Allowed keywords**: github, issues, pull request, repository, etc.

### 2. Repository Analysis (GitHubAnalyzerAgent)  
- **GitHub MCP Tools**: Lists issues and PRs from last 30 days
- **Analysis**: Metrics, trends, urgent items, recommendations
- **Output**: Structured summary with JSON data for storage

### 3. Data Storage (NotionManagerAgent)
- **Notion MCP**: Creates/updates "GitHub Repository Monitoring" database
- **Structure**: Date, repository, metrics, insights, full analysis
- **Forwarding**: Passes complete analysis to email manager

### 4. Email Notification (EmailManagerAgent)
- **HITL Process**: Asks human expert for email approval
- **Human Interface**: Web-based confirmation at localhost:8080
- **Gmail MCP**: Sends professionally formatted reports
- **Format**: Executive summary + detailed analysis + recommendations

## 📊 Example Output

### Analysis Summary
```
=== GITHUB REPOSITORY ANALYSIS ===

🏪 Repository: microsoft/vscode
📅 Analysis Date: 2025-01-13T10:30:00Z  
🔍 Analysis Period: Last 30 days

📊 SUMMARY METRICS
- Issues: 1,245 total (832 open, 413 closed)
- Pull Requests: 156 total (23 open, 125 merged, 3 draft, 5 closed)
- Recent Activity Level: High
- Last Updated: 2 hours ago

🚨 URGENT ITEMS (High Priority)
- Issue #198234: Critical performance regression in editor
- PR #45123: Security fix for extension loading (needs review)
- Issue #198156: Data loss bug in settings sync

[... detailed analysis continues ...]
```

### Human Expert Interaction
```
Human Expert Interface (localhost:8080):

GitHub analysis ready for microsoft/vscode. Key findings: 832 open issues, 3 urgent items.
Activity level: High. Would you like me to email this summary to someone?

> yes
Please provide the recipient's email address(es):
> team-lead@company.com

✅ Email sent successfully to team-lead@company.com
```

## 🛡️ Security Features

### Input Guardrails
- **GitHub-only filtering**: Prevents non-GitHub requests
- **Keyword detection**: "github", "issues", "pull request", etc.
- **Custom messages**: Clear feedback for blocked requests

### Human-in-the-Loop  
- **Email confirmation**: Human approval required for all emails
- **Recipient control**: Human specifies email addresses
- **Content review**: Full analysis available for human review

## 🔧 Troubleshooting

### Common Issues

**"GitHub token invalid"**
- Verify your GitHub personal access token has `repo` scope
- Check token hasn't expired

**"Notion MCP connection failed"**  
- Verify your customer ID in the Notion MCP URL
- Check internet connection and firewall settings

**"Human expert not responding"**
- Ensure web interface is running at localhost:8080
- Check human expert is connected with correct credentials
- Verify 5-minute timeout hasn't expired

**"Agent connection failed"**
- Verify XMPP server is running and accessible
- Check agent credentials and domain name
- Ensure WebSocket support is enabled

### Debug Mode
Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🎯 Customization Options

### Extend Analysis Period
Modify GitHubAnalyzer prompt to analyze different time periods:
```python
"List recent issues (open and closed, last 60 days)"  # Instead of 30 days
```

### Additional MCP Servers
Add more monitoring capabilities:
```python
# Add Jira MCP for issue tracking
jira_mcp = StdioServerConfig(...)

# Add Slack MCP for notifications  
slack_mcp = StdioServerConfig(...)
```

### Custom Guardrails
Extend keyword filtering:
```python
self.github_keywords.extend(["codecov", "ci/cd", "deployment", "release"])
```

### Email Templates
Customize email formatting in EmailManager prompt:
```
Subject: "[URGENT] GitHub Issues Report - [Repository] - [Date]"
```

## 📚 Related Examples

- `human_in_the_loop_example.py` - Basic HITL implementation
- `notion_http_streaming_example.py` - Notion MCP usage
- `guardrails_example.py` - Input/output guardrails
- `valencia_multiagent_trip_planner.py` - Complex multi-agent workflows

## 🤝 Contributing

To extend this example:
1. Add new MCP servers for additional data sources
2. Implement custom guardrails for specific filtering needs
3. Extend human interface with more sophisticated approval workflows
4. Add routing logic for different types of repositories or organizations

---

*This example demonstrates the full power of SPADE_LLM for building production-ready multi-agent systems with safety controls, external integrations, and human oversight.*