# MCP Client Python Example - Setup Guide

This project is an MCP (Model Context Protocol) client with a FastAPI backend and Streamlit frontend that connects to Claude AI (via AWS Bedrock) and supports multiple MCP servers for enhanced functionality.

## Prerequisites

1. **Python 3.10+** ✓
2. **AWS Account with Bedrock Access** - For Claude Sonnet 4.5
3. **AWS Credentials** - Configured locally (via AWS CLI or environment variables)
4. **GitHub Personal Access Token** (Optional) - For GitHub MCP server
5. **Node.js/npx** (Optional) - For Filesystem MCP server

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd /Users/hle/src/github.com/huydinhle/mcp-client-python-example
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

**Important:** Create `.env` file in the `api/` directory (NOT the project root):

```bash
# File: api/.env

# ============================================
# AWS Bedrock Configuration (Required)
# ============================================
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# AWS credentials (if not using default AWS CLI profile)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# AWS_SESSION_TOKEN=your_session_token  # for temporary credentials

# ============================================
# GitHub MCP Server (Optional - for GitHub operations)
# ============================================
MCP_GITHUB_ENABLED=true
MCP_GITHUB_PATH=/path/to/mcp-binaries/github-mcp-server
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
GITHUB_HOST=github.com  # or github.sie.sony.com for enterprise

# ============================================
# Filesystem MCP Server (Optional - for local file access)
# ============================================
MCP_FILESYSTEM_ENABLED=true
MCP_FILESYSTEM_PATH=npx
MCP_FILESYSTEM_ARGS=-y,@modelcontextprotocol/server-filesystem,/path/to/your/monorepo
```

**Replace** paths and tokens with your actual values. See detailed guides below for setup.

### 3. MCP Servers Setup

This client supports **multiple MCP servers** running simultaneously. You can enable/disable them individually.

#### Option A: GitHub MCP Server (Recommended)

Provides 40+ tools for GitHub operations (read files, search code, create PRs, etc.)

1. **Download the binary:**
   ```bash
   mkdir -p mcp-binaries
   cd mcp-binaries
   # Download from https://github.com/github/github-mcp-server/releases
   # Make it executable:
   chmod +x github-mcp-server
   ```

2. **Configure in `api/.env`:**
   ```bash
   MCP_GITHUB_ENABLED=true
   MCP_GITHUB_PATH=/path/to/mcp-binaries/github-mcp-server
   GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
   GITHUB_HOST=github.com  # or your enterprise GitHub URL
   ```

3. **Get a GitHub token:** https://github.com/settings/tokens (needs `repo` scope)

#### Option B: Filesystem MCP Server (Recommended)

Allows Claude to read/search files from your local filesystem.

1. **No installation needed!** Uses `npx` to run on-demand.

2. **Configure in `api/.env`:**
   ```bash
   MCP_FILESYSTEM_ENABLED=true
   MCP_FILESYSTEM_PATH=npx
   MCP_FILESYSTEM_ARGS=-y,@modelcontextprotocol/server-filesystem,/path/to/your/code
   ```

3. **Security:** Only directories you specify will be accessible.

#### Option C: Custom MCP Server

You can still use custom Python-based MCP servers:

```bash
cd /path/to/your/mcp-server
uv sync  # Install dependencies
```

**Note:** Each MCP server runs as an independent process managed by the backend.

### 4. Running the Application

The application has two components that need to run simultaneously in separate terminals:

#### Terminal 1 - Backend API (FastAPI)

```bash
cd /Users/hle/src/github.com/huydinhle/mcp-client-python-example
source venv/bin/activate

# Export AWS profile if needed
export AWS_PROFILE=bedrock
export AWS_DEFAULT_PROFILE=bedrock

cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
INFO:     ✅ Connected to github MCP server. Tools: ['get_file_contents', 'search_code', ...]
INFO:     ✅ Connected to filesystem MCP server. Tools: ['read_file', 'list_directory', ...]
INFO:     ✅ Successfully connected to 2 server(s): ['github', 'filesystem']
INFO:     Total tools available: 54
```

**Note:** If you only enabled one server, you'll see fewer tools.

#### Terminal 2 - Frontend (Streamlit)

```bash
cd /Users/hle/src/github.com/huydinhle/mcp-client-python-example
source venv/bin/activate
cd front
STREAMLIT_SERVER_HEADLESS=true streamlit run main.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### 5. Access the Application

- **Frontend UI:** http://localhost:8501 (Streamlit chat interface)
- **Backend API:** http://localhost:8000 (FastAPI REST API)
- **API Docs:** http://localhost:8000/docs (Swagger UI)

## Project Structure

```
.
├── api/                    # FastAPI backend
│   ├── .env               # Environment variables (API keys, server path)
│   ├── main.py            # API endpoints
│   ├── mcp_client.py      # MCP client implementation
│   ├── requirements.txt   # Backend-specific dependencies
│   └── utils/
│       └── logger.py      # Logging utilities
├── front/                 # Streamlit frontend
│   ├── main.py           # Main entry point
│   ├── chatbot.py        # UI components
│   └── utils/
│       └── logger.py     # Logging utilities
├── requirements.txt      # Project-wide Python dependencies
├── venv/                 # Virtual environment
└── conversations/        # Auto-generated conversation logs
```

## How It Works

1. **Backend (FastAPI):** 
   - Loads configuration from `api/.env`
   - Connects to **multiple MCP servers** simultaneously (GitHub, Filesystem, etc.)
   - Manages communication with **Claude Sonnet 4.5** via **AWS Bedrock**
   - Routes tool calls to the appropriate MCP server
   - Exposes REST API endpoints for the frontend
   - Logs conversations to `conversations/` directory

2. **Frontend (Streamlit):**
   - Provides a chat interface at http://localhost:8501
   - Sends user queries to the backend API
   - Displays responses and tool calls (with JSON/text handling)
   - Shows available tools in the sidebar
   - **Maintains conversation history** - follow-up questions work!

3. **MCP Servers:**
   - **GitHub MCP:** 40+ tools for GitHub operations (get files, search code, create PRs, etc.)
   - **Filesystem MCP:** Tools for reading local files, listing directories, searching files
   - **Custom MCP:** You can add your own Python/Node.js MCP servers
   - Each runs as a separate process launched by the backend
   - Backend aggregates tools from all connected servers

## Key Features & Limitations

### Current Features

✅ **Working:**
- **AWS Bedrock Integration** - Claude Sonnet 4.5 via Bedrock
- **Multiple MCP Servers** - GitHub + Filesystem + custom servers simultaneously
- **Conversation History** - Follow-up questions work!
- **54+ Tools** - GitHub operations + local file access
- **Smart Tool Routing** - Automatically routes tool calls to correct server
- **Toggleable Servers** - Enable/disable servers via `.env` flags
- **JSON and Text Display** - Handles various tool result formats
- **API Endpoints** - Direct backend access for integration
- **Conversation Logging** - JSON logs in `conversations/` directory

### Limitations

⚠️ **Current Limitations:**
- Conversation history persists until server restart (no database)
- No "Clear Chat" button in UI yet (restart server to clear)
- Filesystem MCP only accesses directories you explicitly allow
- GitHub MCP requires valid personal access token
- AWS Bedrock requires proper IAM permissions

### Conversation History

The chatbot **DOES** maintain conversation history:
- ✅ Follow-up questions work
- ✅ Claude remembers previous context
- ✅ Multi-turn conversations supported
- ⚠️ History clears on server restart

**To clear conversation manually:** Restart the backend server.

## Troubleshooting

### "Failed to call LLM via Bedrock: Unable to locate credentials"

**Problem:** AWS credentials not configured

**Solution:**
```bash
# Option 1: Use AWS CLI to configure credentials
aws configure --profile bedrock

# Option 2: Export environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-west-2

# Option 3: Add to api/.env
AWS_REGION=us-west-2
# AWS_ACCESS_KEY_ID=your_key  # (optional if using AWS CLI profile)
# AWS_SECRET_ACCESS_KEY=your_secret
```

Then restart the backend with:
```bash
export AWS_PROFILE=bedrock
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### "Failed to connect to any MCP servers"

**Problem:** No MCP servers enabled or paths incorrect

**Solution:**
1. Check your `api/.env` - at least one server must be enabled:
   ```bash
   MCP_GITHUB_ENABLED=true  # OR
   MCP_FILESYSTEM_ENABLED=true
   ```

2. Verify paths are correct:
   ```bash
   # For GitHub MCP
   ls -la /path/to/mcp-binaries/github-mcp-server
   
   # For Filesystem MCP (npx should be in PATH)
   which npx
   ```

3. Check backend logs for specific connection errors

### "Access denied - path outside allowed directories"

**Problem:** Filesystem MCP trying to access path outside configured directory

**Solution:** This is normal security behavior. Update `MCP_FILESYSTEM_ARGS` in `api/.env`:
```bash
MCP_FILESYSTEM_ARGS=-y,@modelcontextprotocol/server-filesystem,/your/desired/path
```

### "Tool execution failed: 'MCPClient' object has no attribute 'session'"

**Problem:** Code version mismatch

**Solution:** This was fixed in the latest version. Pull latest changes:
```bash
git pull origin main
# Restart backend
```

### GitHub MCP: "failed to parse API host"

**Problem:** `GITHUB_HOST` needs full URL with protocol

**Solution:** Update in `api/.env`:
```bash
# Wrong:
GITHUB_HOST=github.sie.sony.com

# Correct:
GITHUB_HOST=https://github.sie.sony.com
```

### Backend fails to start with "ValidationError"

**Problem:** Missing required environment variables

**Solution:** Ensure all required fields are in `api/.env`:
```bash
# Required:
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# At least one server must be enabled:
MCP_GITHUB_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
```

### Port already in use

**Error:** `Address already in use` on port 8000 or 8501

**Solution:**
```bash
# Kill processes on port 8000
lsof -ti:8000 | xargs kill -9

# Kill processes on port 8501  
lsof -ti:8501 | xargs kill -9
```

## Testing the Application

### Example Queries

#### With GitHub MCP Server:

✅ **GitHub Operations:**
- "Get the README.md from the SIE/monorepo repository"
- "Search for Python files that contain 'NewDatabricksRoleStack' in the monorepo"
- "Show me the latest issues in the kubernetes/kubernetes repository"
- "What are the main directories in the tensorflow/tensorflow repo?"

#### With Filesystem MCP Server:

✅ **Local File Operations:**
- "List the files in the monorepo root directory"
- "Read the README.md file from my local monorepo"
- "Search for all Go files in the local monorepo"
- "What is the directory structure of my local project?"

#### With Both Servers (Powerful!):

✅ **Compare & Analyze:**
- "Compare the local README.md with the one on GitHub SIE/monorepo"
- "Explain what NewDatabricksRoleStack does in the local pulumi code"
- "Are there any files in my local project that don't exist in the GitHub repo?"
- "Summarize the monorepo directory and explain its purpose"

#### Test with curl:

```bash
# Test GitHub MCP
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Get the README from SIE/monorepo repository"}' \
  --no-buffer

# Test Filesystem MCP
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List the files in the monorepo directory"}' \
  --no-buffer

# Test Combined
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain NewDatabricksRoleStack in pulumi from local files"}' \
  --no-buffer
```

## API Reference

### POST /query
Process a query using Claude Sonnet 4.5 and available MCP tools

**Request:**
```json
{
  "query": "Explain NewDatabricksRoleStack in pulumi from local files"
}
```

**Response:**
```json
{
  "messages": [
    {"role": "user", "content": "Explain NewDatabricksRoleStack..."},
    {"role": "assistant", "content": [
      {"type": "text", "text": "I'll search for that..."},
      {"type": "tool_use", "id": "...", "name": "search_files", "input": {...}}
    ]},
    {"role": "user", "content": [
      {"type": "tool_result", "tool_use_id": "...", "content": "..."}
    ]},
    {"role": "assistant", "content": "Here's what I found..."}
  ]
}
```

### GET /tools
Get list of all available MCP tools from connected servers

**Response:**
```json
{
  "tools": [
    {
      "name": "get_file_contents",
      "description": "Get the contents of a file from GitHub...",
      "input_schema": {"type": "object", "properties": {...}}
    },
    {
      "name": "read_file",
      "description": "Read complete contents of a file...",
      "input_schema": {"type": "object", "properties": {...}}
    },
    ...
  ]
}
```

### POST /tool
Call a specific MCP tool directly (bypasses Claude)

**Request:**
```json
{
  "name": "read_file",
  "args": {
    "path": "/path/to/file.py"
  }
}
```

**Response:**
```json
{
  "content": [
    {"type": "text", "text": "# File contents here..."}
  ]
}
```

## Development Tips

1. **Check logs:** Conversation logs are saved to `conversations/` directory
2. **Monitor backend:** Watch Terminal 1 for tool execution and API calls
3. **Debug frontend:** Streamlit shows errors in the browser
4. **Test API directly:** Use http://localhost:8000/docs for Swagger UI
5. **Restart on changes:** Backend auto-reloads with `--reload` flag
6. **Toggle MCP servers:** Edit `.env` and set `MCP_*_ENABLED=true/false`
7. **Test tools:** Use `curl http://localhost:8000/tools` to see available tools
8. **AWS Profile:** Remember to export `AWS_PROFILE` if using named profiles

## Next Steps

- ✅ Configure AWS Bedrock credentials
- ✅ Set up your `api/.env` file with Bedrock and MCP server configs
- ✅ Enable at least one MCP server (GitHub or Filesystem recommended)
- ✅ Run both backend and frontend
- ✅ Start chatting with 54+ tools!

## Getting Credentials

- **AWS Bedrock Access:** Contact your AWS administrator or configure via AWS Console
  - Requires: `bedrock:InvokeModel` IAM permission
  - Model: `global.anthropic.claude-sonnet-4-5-20250929-v1:0`
  
- **GitHub Personal Access Token:** https://github.com/settings/tokens
  - Required scope: `repo` (Full control of private repositories)
  - For enterprise GitHub: Use your enterprise GitHub URL

- **No other API keys needed!** Filesystem MCP uses `npx` (no installation required)

## Additional Resources

### Detailed Setup Guides

- **[AWS Bedrock Setup Guide](./AWS_BEDROCK_SETUP.md)** - Comprehensive AWS Bedrock configuration
- **[Multiple MCP Servers Setup](./MULTI_MCP_SETUP.md)** - How to configure GitHub and Filesystem MCP servers

### Documentation

- **MCP Documentation:** https://modelcontextprotocol.io/
- **AWS Bedrock:** https://aws.amazon.com/bedrock/
- **GitHub MCP Server:** https://github.com/github/github-mcp-server
- **Filesystem MCP Server:** https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Streamlit Docs:** https://docs.streamlit.io/

---

## Quick Reference

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    User (Browser)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Streamlit Frontend (Port 8501)                     │
│  • Chat Interface                                            │
│  • Tool Result Display                                       │
│  • Conversation History                                      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           FastAPI Backend (Port 8000)                        │
│  • MCPClient (manages multiple servers)                     │
│  • Tool routing                                              │
│  • Conversation logging                                      │
└────────┬────────────────────────────┬──────────────────┬────┘
         │                            │                  │
         ▼                            ▼                  ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐
│  AWS Bedrock    │    │  GitHub MCP      │    │ Filesystem   │
│                 │    │  Server          │    │ MCP Server   │
│  Claude Sonnet  │    │  (40 tools)      │    │ (14 tools)   │
│  4.5            │    │                  │    │              │
└─────────────────┘    └──────────────────┘    └──────────────┘
```

### Key Files
- `api/.env` - All configuration (AWS, GitHub token, MCP paths)
- `api/main.py` - FastAPI endpoints & server initialization
- `api/mcp_client.py` - MCP client & AWS Bedrock integration
- `front/main.py` - Streamlit UI entry point
- `front/chatbot.py` - Chat interface & message display

### Available Tools (54 total)
- **GitHub MCP (40):** `get_file_contents`, `search_code`, `list_issues`, `create_pull_request`, etc.
- **Filesystem MCP (14):** `read_file`, `list_directory`, `search_files`, `get_file_info`, etc.
