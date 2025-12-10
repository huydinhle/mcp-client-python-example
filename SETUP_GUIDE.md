# MCP Client Python Example - Setup Guide

This project is an MCP (Model Context Protocol) client with a FastAPI backend and Streamlit frontend that connects to Claude AI and allows interaction with MCP servers.

## Prerequisites

1. **Python 3.10+** ✓
2. **Anthropic API Key** - Get one from https://console.anthropic.com/
3. **MCP Server** - You need an MCP server script to connect to
4. **SERPER API Key** (Optional) - For web search functionality in MCP server

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

# Required: Your Anthropic API key for Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required: Path to your MCP server script
SERVER_SCRIPT_PATH=/path/to/your/mcp/server/main.py

# Optional: For web search functionality (used by some MCP servers)
SERPER_API_KEY=your_serper_api_key_here
```

**Replace** these values with your actual API keys and server path.

### 3. MCP Server Setup

If you're using the example MCP server at `/Users/hle/src/github.com/alejandro-ao/mcp-server-example/`:

#### Install MCP Server Dependencies

```bash
cd /Users/hle/src/github.com/alejandro-ao/mcp-server-example
uv sync
```

#### Create MCP Server .env File

The MCP server runs in its own environment and needs its own `.env` file:

```bash
# File: /Users/hle/src/github.com/alejandro-ao/mcp-server-example/.env

SERPER_API_KEY=your_serper_api_key_here
```

**Note:** This is separate from the client's `.env` file because the MCP server runs as an independent process.

### 4. Running the Application

The application has two components that need to run simultaneously in separate terminals:

#### Terminal 1 - Backend API (FastAPI)

```bash
cd /Users/hle/src/github.com/huydinhle/mcp-client-python-example
source venv/bin/activate
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
INFO:     Successfully connected to server. Available tools: ['get_docs']
```

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
   - Connects to the MCP server using `uv run` (for uv-based servers) or `python`
   - Manages communication with Claude AI (currently using Claude 3 Haiku)
   - Exposes REST API endpoints for the frontend
   - Logs conversations to `conversations/` directory

2. **Frontend (Streamlit):**
   - Provides a chat interface at http://localhost:8501
   - Sends user queries to the backend API
   - Displays responses and tool calls
   - Shows available tools in the sidebar
   - **Note:** Currently stateless - each query is independent (no conversation history)

3. **MCP Server:**
   - Runs as a separate process launched by the backend
   - Provides tools/functions that Claude can call
   - Example tool: `get_docs` - Searches documentation using Google Serper API
   - Has its own `.env` file for API keys it needs

## Key Features & Limitations

### Current Behavior

✅ **Working:**
- MCP server connection with auto-detection of `uv`-based projects
- Claude 3 Haiku with 4096 max tokens
- Tool calling (e.g., `get_docs` for documentation search)
- JSON and text tool result display
- API endpoint for direct queries
- Conversation logging to JSON files

❌ **Limitations:**
- No conversation history between queries (each query is independent)
- Frontend replaces all messages on each query
- Backend clears conversation history on each query

### Conversation History

Currently, the chatbot does **NOT** maintain conversation history:
- Each query is treated as completely independent
- Claude has no awareness of previous questions or answers
- Follow-up questions won't work (e.g., "Tell me more about that")

This was intentional to prevent:
- Context pollution from failed tool attempts
- Token limit issues with long conversations
- Confusion from accumulated context

If you want to enable conversation history, you'll need to modify:
1. `api/mcp_client.py` - Remove `self.messages = []` in `process_query()`
2. `front/chatbot.py` - Use `extend()` instead of replacing messages
3. Add a "Clear Chat" button in the UI

## Troubleshooting

### Backend fails to start with "ValidationError"
**Error:** `Extra inputs are not permitted [type=extra_forbidden]`

**Solution:** Make sure your `Settings` class in `api/main.py` includes all fields in your `.env` file:
```python
class Settings(BaseSettings):
    server_script_path: str
    anthropic_api_key: str = ""
    serper_api_key: str = ""
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields
```

### "Failed to connect to server" or "ModuleNotFoundError"

**Problem:** MCP server dependencies not installed

**Solution:** 
```bash
cd /path/to/your/mcp/server
uv sync  # For uv-based projects
# OR
pip install -r requirements.txt  # For pip-based projects
```

### "ANTHROPIC_API_KEY not found"

**Problem:** `.env` file in wrong location or not formatted correctly

**Solution:**
- Ensure `.env` is in the `api/` directory (not project root)
- Check file formatting (no quotes around values needed)
- Verify API key is valid at https://console.anthropic.com/

### "Error code: 404 - model: claude-3-5-sonnet-20241022"

**Problem:** API key doesn't have access to requested model

**Solution:** The code currently uses Claude 3 Haiku (`claude-3-haiku-20240307`). If you want to use a different model, edit `api/mcp_client.py` line 122 and change the model name to one your API key supports.

### "SERPER_API_KEY not configured" in tool results

**Problem:** MCP server can't access SERPER_API_KEY

**Solution:**
- Create `.env` file in the **MCP server's directory** (not just the client)
- Add `SERPER_API_KEY=your_key_here`
- Restart the backend so it reconnects to the MCP server

### Frontend JSONDecodeError

**Problem:** Fixed in latest version, but if you see it, the frontend is trying to parse text as JSON

**Solution:** Update `front/chatbot.py` to handle both JSON and text tool results with try/except

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

### Good Example Queries

These queries should work well with the `get_docs` tool:

✅ **LangChain:**
- "How do I use embeddings in langchain?"
- "What are LangChain agents?"
- "How to create chains in langchain?"

✅ **OpenAI:**
- "What is the OpenAI chat completion API?"
- "How do I use OpenAI embeddings?"

✅ **LLama-index:**
- "What are vector stores in llama-index?"
- "How to build a query engine?"

❌ **Queries that may not work well:**
- Topics not well-documented in the specific docs sites
- Very new features not yet in documentation
- ChromaDB in langchain (not extensively documented there)

## API Reference

### POST /query
Process a query using Claude and MCP tools

**Request:**
```json
{
  "query": "How do I use embeddings in langchain?"
}
```

**Response:**
```json
{
  "messages": [
    {"role": "user", "content": "How do I use embeddings in langchain?"},
    {"role": "assistant", "content": [...]},
    ...
  ]
}
```

### GET /tools
Get list of available MCP tools

**Response:**
```json
{
  "tools": [
    {
      "name": "get_docs",
      "description": "Search the latest docs...",
      "input_schema": {...}
    }
  ]
}
```

### POST /tool
Call a specific MCP tool directly

**Request:**
```json
{
  "name": "get_docs",
  "args": {
    "query": "embeddings",
    "library": "langchain"
  }
}
```

## Development Tips

1. **Check logs:** Conversation logs are saved to `conversations/` directory
2. **Monitor backend:** Watch Terminal 1 for tool execution and API calls
3. **Debug frontend:** Streamlit shows errors in the browser
4. **Test API directly:** Use http://localhost:8000/docs for Swagger UI
5. **Restart on changes:** Backend auto-reloads with `--reload` flag

## Next Steps

- ✅ Set up your `.env` file in `api/` directory with valid credentials
- ✅ Ensure MCP server dependencies are installed
- ✅ Create MCP server's `.env` file if needed
- ✅ Run both backend and frontend
- ✅ Start chatting!

## Getting API Keys

- **Anthropic API Key:** https://console.anthropic.com/ (Required)
- **Serper API Key:** https://serper.dev/ (Optional, for documentation search)

## Additional Resources

- **MCP Documentation:** https://modelcontextprotocol.io/
- **LangChain Docs:** https://python.langchain.com/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Streamlit Docs:** https://docs.streamlit.io/
