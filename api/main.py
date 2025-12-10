from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from contextlib import asynccontextmanager
from mcp_client import MCPClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Legacy single server config (backward compatibility)
    server_script_path: str = ""
    
    # MCP Server configurations
    mcp_github_enabled: bool = True
    mcp_github_path: str = ""
    mcp_filesystem_enabled: bool = False
    mcp_filesystem_path: str = "npx"
    mcp_filesystem_args: str = ""  # Comma-separated args
    
    # API keys and credentials
    anthropic_api_key: str = ""
    serper_api_key: str = ""
    github_personal_access_token: str = ""
    github_host: str = ""
    
    # AWS Bedrock
    aws_region: str = "us-west-2"
    bedrock_model_id: str = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    client = MCPClient()
    try:
        # Build server configurations
        server_configs = []
        
        # GitHub MCP Server
        if settings.mcp_github_enabled and settings.mcp_github_path:
            github_args = ["stdio"]
            if settings.github_host:
                github_args.extend(["--gh-host", f"https://{settings.github_host}" if not settings.github_host.startswith("http") else settings.github_host])
            
            server_configs.append({
                "name": "github",
                "path": settings.mcp_github_path,
                "args": github_args,
                "enabled": True
            })
        
        # Filesystem MCP Server
        if settings.mcp_filesystem_enabled and settings.mcp_filesystem_path:
            fs_args = []
            if settings.mcp_filesystem_args:
                # Parse comma-separated args
                fs_args = [arg.strip() for arg in settings.mcp_filesystem_args.split(",")]
            
            server_configs.append({
                "name": "filesystem",
                "path": settings.mcp_filesystem_path,
                "args": fs_args,
                "enabled": True
            })
        
        # Fallback to legacy single server config if no new configs
        if not server_configs and settings.server_script_path:
            connected = await client.connect_to_server(settings.server_script_path)
            if not connected:
                raise Exception("Failed to connect to server")
        elif server_configs:
            # Connect to multiple servers
            connected = await client.connect_to_multiple_servers(server_configs)
            if not connected:
                raise Exception("Failed to connect to any servers")
        else:
            raise Exception("No MCP servers configured. Set MCP_GITHUB_PATH or MCP_FILESYSTEM_PATH in .env")
        
        app.state.client = client
        yield
    except Exception as e:
        raise Exception(f"Failed to connect to server: {str(e)}")
    finally:
        # Shutdown
        await client.cleanup()

app = FastAPI(title="MCP Chatbot API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class QueryRequest(BaseModel):
    query: str

class Message(BaseModel):
    role: str
    content: Any

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]

@app.get("/tools")
async def get_available_tools():
    """Get list of available tools"""
    try:
        tools = await app.state.client.get_mcp_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in tools
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def process_query(request: QueryRequest):
    """Process a query and return the response"""
    try:
        messages = []
        messages = await app.state.client.process_query(request.query)
        # async for message in app.state.client.process_query(request.query):
        #     messages.append(message)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool")
async def call_tool(tool_call: ToolCall):
    """Call a specific tool"""
    try:
        result = await app.state.client.call_tool(tool_call.name, tool_call.args)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)