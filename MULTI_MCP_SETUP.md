# Multiple MCP Servers Setup Guide

This guide shows you how to use multiple MCP servers simultaneously (GitHub + Filesystem).

## Quick Start

Add these to your `api/.env` file:

```bash
# ============================================
# MCP Server Configuration
# ============================================

# GitHub MCP Server (for GitHub operations)
MCP_GITHUB_ENABLED=true
MCP_GITHUB_PATH=/Users/hle/src/github.com/huydinhle/mcp-client-python-example/mcp-binaries/github-mcp-server
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
GITHUB_HOST=github.sie.sony.com

# Filesystem MCP Server (for local file access)
MCP_FILESYSTEM_ENABLED=true
MCP_FILESYSTEM_PATH=npx
MCP_FILESYSTEM_ARGS=-y,@modelcontextprotocol/server-filesystem,/Users/hle/path/to/your/monorepo

# AWS Bedrock
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
```

**Important:** Update the `MCP_FILESYSTEM_ARGS` path to point to your actual monorepo directory!

Example for your setup:
```bash
MCP_FILESYSTEM_ARGS=-y,@modelcontextprotocol/server-filesystem,/Users/hle/monorepo
```

## Filesystem MCP Server Setup

The filesystem MCP server allows Claude to read files from your local filesystem.

### Option 1: Using npx (Easiest)

No installation needed! Just configure in `.env`:

```bash
MCP_FILESYSTEM_ENABLED=true
MCP_FILESYSTEM_PATH=npx
MCP_FILESYSTEM_ARGS=-y,@modelcontextprotocol/server-filesystem,/Users/hle/path/to/your/monorepo
```

### Option 2: Install Locally

```bash
npm install -g @modelcontextprotocol/server-filesystem
```

Then configure:
```bash
MCP_FILESYSTEM_PATH=server-filesystem
MCP_FILESYSTEM_ARGS=/Users/hle/path/to/your/monorepo
```

## Security Note

⚠️ **Important:** The filesystem MCP server will have read access to the paths you specify. Only provide paths to directories you want Claude to access.

## Available Tools After Setup

### GitHub MCP Tools (~40 tools):
- `get_file_contents` - Get file from GitHub
- `search_code` - Search code in GitHub
- `list_issues` - List repository issues
- `create_pull_request` - Create PRs
- And many more...

### Filesystem MCP Tools:
- `read_file` - Read local files
- `list_directory` - List directory contents
- `search_files` - Search for files
- `get_file_info` - Get file metadata

## Example Queries

With both servers enabled, you can do:

```
"Compare the README.md in the GitHub SIE/monorepo with my local monorepo at /Users/hle/monorepo"
```

```
"Read the main.py file from my local project and suggest improvements"
```

```
"List all Python files in my local monorepo and check if they exist in GitHub"
```

## Toggling Servers On/Off

Simply update your `.env` file:

```bash
# Enable both
MCP_GITHUB_ENABLED=true
MCP_FILESYSTEM_ENABLED=true

# Only GitHub
MCP_GITHUB_ENABLED=true
MCP_FILESYSTEM_ENABLED=false

# Only Filesystem
MCP_GITHUB_ENABLED=false
MCP_FILESYSTEM_ENABLED=true
```

Then restart the backend server!

## Troubleshooting

### "No tools available"
- Check that at least one server is enabled
- Verify the server paths are correct
- Check the terminal logs for connection errors

### "Tool not found"
- Check which servers are enabled
- The tool might be from a disabled server
- Run `curl http://localhost:8000/tools` to see available tools

