from typing import Optional
from contextlib import AsyncExitStack
import traceback
from utils.logger import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from datetime import datetime
import json
import os
import boto3


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Initialize AWS Bedrock client
        aws_region = os.getenv("AWS_REGION", "us-west-2")
        self.llm = boto3.client(
            service_name='bedrock-runtime',
            region_name=aws_region
        )
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-5-20250929-v1:0")
        
        self.tools = []
        self.messages = []
        self.logger = logger

    async def call_tool(self, tool_name: str, tool_args: dict):
        """Call a tool with the given name and arguments"""
        try:
            result = await self.session.call_tool(tool_name, tool_args)
            return result
        except Exception as e:
            self.logger.error(f"Failed to call tool: {str(e)}")
            raise Exception(f"Failed to call tool: {str(e)}")

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py, .js, or binary executable)
        """
        try:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            is_executable = os.access(server_script_path, os.X_OK)

            self.logger.info(
                f"Attempting to connect to server using script: {server_script_path}"
            )
            
            # Prepare environment variables for the MCP server
            # Include all environment variables it might need
            server_env = os.environ.copy()
            
            # Check if the server uses uv (has pyproject.toml or uv.lock)
            server_dir = os.path.dirname(server_script_path)
            server_filename = os.path.basename(server_script_path)
            has_pyproject = os.path.exists(os.path.join(server_dir, "pyproject.toml"))
            has_uv_lock = os.path.exists(os.path.join(server_dir, "uv.lock"))
            
            if is_python and (has_pyproject or has_uv_lock):
                # Use uv run for uv-based projects (run from server directory)
                command = "uv"
                args = ["run", server_filename]
                server_env["UV_PROJECT_ENVIRONMENT"] = os.path.join(server_dir, ".venv")
                self.logger.info(f"Detected uv project, using 'uv run' from {server_dir}")
                server_params = StdioServerParameters(
                    command=command, args=args, env=server_env, cwd=server_dir
                )
            elif is_executable and not is_python and not is_js:
                # Binary executable (like github-mcp-server)
                command = server_script_path
                # GitHub MCP server requires 'stdio' subcommand
                if 'github' in server_filename.lower():
                    args = ["stdio"]
                    # Add gh-host flag if GitHub Enterprise (needs full URL with https://)
                    github_host = os.getenv("GITHUB_HOST", "")
                    if github_host and "github.com" not in github_host:
                        # Ensure it has a scheme
                        if not github_host.startswith(("http://", "https://")):
                            github_host = f"https://{github_host}"
                        args.extend(["--gh-host", github_host])
                    self.logger.info(f"Detected GitHub MCP server binary with args: {args}")
                else:
                    args = []
                    self.logger.info(f"Detected binary executable: {server_filename}")
                server_params = StdioServerParameters(
                    command=command, args=args, env=server_env
                )
            elif is_python or is_js:
                # Use standard python or node
                command = "python" if is_python else "node"
                args = [server_script_path]
                server_params = StdioServerParameters(
                    command=command, args=args, env=server_env
                )
            else:
                raise ValueError(f"Server path must be a .py, .js, or executable file: {server_script_path}")

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            await self.session.initialize()
            mcp_tools = await self.get_mcp_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in mcp_tools
            ]
            self.logger.info(
                f"Successfully connected to server. Available tools: {[tool['name'] for tool in self.tools]}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {str(e)}")
            self.logger.debug(f"Connection error details: {traceback.format_exc()}")
            raise Exception(f"Failed to connect to server: {str(e)}")

    async def get_mcp_tools(self):
        try:
            self.logger.info("Requesting MCP tools from the server.")
            response = await self.session.list_tools()
            tools = response.tools
            return tools
        except Exception as e:
            self.logger.error(f"Failed to get MCP tools: {str(e)}")
            self.logger.debug(f"Error details: {traceback.format_exc()}")
            raise Exception(f"Failed to get tools: {str(e)}")

    async def call_llm(self):
        """Call the LLM via AWS Bedrock"""
        try:
            # Prepare the request body for Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 8192,
                "messages": self.messages,
            }
            
            # Add tools if available
            if self.tools:
                request_body["tools"] = self.tools
            
            # Call Bedrock
            response = self.llm.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Create a simple object to mimic Anthropic's Message type
            class BedrockResponse:
                def __init__(self, response_data):
                    self.content = []
                    self.stop_reason = response_data.get('stop_reason')
                    self.id = response_data.get('id')
                    
                    # Convert content to match Anthropic's format
                    for item in response_data.get('content', []):
                        if item['type'] == 'text':
                            self.content.append(type('TextBlock', (), {
                                'type': 'text',
                                'text': item['text']
                            })())
                        elif item['type'] == 'tool_use':
                            self.content.append(type('ToolUseBlock', (), {
                                'type': 'tool_use',
                                'id': item['id'],
                                'name': item['name'],
                                'input': item['input']
                            })())
                
                def to_dict(self):
                    content_list = []
                    for c in self.content:
                        if c.type == 'text':
                            content_list.append({
                                'type': 'text',
                                'text': c.text
                            })
                        elif c.type == 'tool_use':
                            content_list.append({
                                'type': 'tool_use',
                                'id': c.id,
                                'name': c.name,
                                'input': c.input
                            })
                    return {'content': content_list}
            
            return BedrockResponse(response_body)
            
        except Exception as e:
            self.logger.error(f"Failed to call LLM via Bedrock: {str(e)}")
            self.logger.debug(f"Error details: {traceback.format_exc()}")
            raise Exception(f"Failed to call LLM via Bedrock: {str(e)}")

    async def process_query(self, query: str):
        """Process a query using Claude and available tools, returning all messages at the end"""
        try:
            self.logger.info(
                f"Processing new query: {query[:100]}..."
            )  # Log first 100 chars of query

            # Clear previous conversation history for independent queries
            self.messages = []
            
            # Add the initial user message
            user_message = {"role": "user", "content": query}
            self.messages.append(user_message)
            await self.log_conversation(self.messages)
            messages = [user_message]

            while True:
                self.logger.debug("Calling Claude API")
                response = await self.call_llm()

                # If it's a simple text response
                if response.content[0].type == "text" and len(response.content) == 1:
                    assistant_message = {
                        "role": "assistant",
                        "content": response.content[0].text,
                    }
                    self.messages.append(assistant_message)
                    await self.log_conversation(self.messages)
                    messages.append(assistant_message)
                    break

                # For more complex responses with tool calls
                assistant_message = {
                    "role": "assistant",
                    "content": response.to_dict()["content"],
                }
                self.messages.append(assistant_message)
                await self.log_conversation(self.messages)
                messages.append(assistant_message)

                for content in response.content:
                    if content.type == "text":
                        # Text content within a complex response
                        text_message = {"role": "assistant", "content": content.text}
                        await self.log_conversation(self.messages)
                        messages.append(text_message)
                    elif content.type == "tool_use":
                        tool_name = content.name
                        tool_args = content.input
                        tool_use_id = content.id

                        self.logger.info(
                            f"Executing tool: {tool_name} with args: {tool_args}"
                        )
                        try:
                            # turn this one return a simple string
                            result = await self.session.call_tool(tool_name, tool_args)
                            self.logger.info(f"Tool result: {result}")
                            
                            # Convert MCP tool result content to Bedrock-compatible format
                            # Bedrock expects simpler format for tool results
                            result_text_parts = []
                            for item in result.content:
                                if hasattr(item, 'type'):
                                    if item.type == 'text':
                                        result_text_parts.append(item.text)
                                    elif item.type == 'resource':
                                        # EmbeddedResource needs to be converted to text
                                        if hasattr(item, 'resource') and hasattr(item.resource, 'text'):
                                            result_text_parts.append(item.resource.text)
                                        elif hasattr(item, 'resource'):
                                            result_text_parts.append(str(item.resource))
                                    else:
                                        result_text_parts.append(str(item))
                                else:
                                    result_text_parts.append(str(item))
                            
                            # Combine all text parts into a single string
                            combined_result = "\n".join(result_text_parts)
                            
                            tool_result_message = {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_id,
                                        "content": combined_result,
                                    }
                                ],
                            }
                            self.messages.append(tool_result_message)
                            await self.log_conversation(self.messages)
                            messages.append(tool_result_message)
                        except Exception as e:
                            error_msg = f"Tool execution failed: {str(e)}"
                            self.logger.error(error_msg)
                            raise Exception(error_msg)

            return messages

        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            self.logger.debug(
                f"Query processing error details: {traceback.format_exc()}"
            )
            raise

    async def log_conversation(self, conversation: list):
        """Log the conversation to json file"""
        # Create conversations directory if it doesn't exist
        os.makedirs("conversations", exist_ok=True)

        # Convert conversation to JSON-serializable format
        serializable_conversation = []
        for message in conversation:
            try:
                serializable_message = {
                    "role": message["role"],
                    "content": []
                }
                
                # Handle both string and list content
                if isinstance(message["content"], str):
                    serializable_message["content"] = message["content"]                  
                elif isinstance(message["content"], list):
                    for content_item in message["content"]:
                        if hasattr(content_item, 'to_dict'):
                            serializable_message["content"].append(content_item.to_dict())
                        elif hasattr(content_item, 'dict'):
                            serializable_message["content"].append(content_item.dict())
                        elif hasattr(content_item, 'model_dump'):
                            serializable_message["content"].append(content_item.model_dump())
                        else:
                            serializable_message["content"].append(content_item)
                
                serializable_conversation.append(serializable_message)
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                self.logger.debug(f"Message content: {message}")
                raise

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join("conversations", f"conversation_{timestamp}.json")
        
        try:
            with open(filepath, "w") as f:
                json.dump(serializable_conversation, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error writing conversation to file: {str(e)}")
            self.logger.debug(f"Serializable conversation: {serializable_conversation}")
            raise

    async def cleanup(self):
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up resources")
            await self.exit_stack.aclose()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
