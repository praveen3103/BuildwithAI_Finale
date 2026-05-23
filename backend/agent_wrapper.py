import os
import sys
import json
import logging
from typing import Any, List, Dict, Callable, Optional, AsyncIterator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_wrapper")

# Try importing the real google-antigravity SDK
try:
    from google.antigravity import Agent as RealAgent
    from google.antigravity.connections.local import LocalAgentConfig as RealConfig
    from google.antigravity.hooks import hooks as real_hooks
    from google.antigravity import types as real_types
    
    HAS_REAL_SDK = True
    logger.info("Imported real google-antigravity SDK successfully!")
    
    Agent = RealAgent
    LocalAgentConfig = RealConfig
    hooks = real_hooks
    types = real_types

except ImportError:
    HAS_REAL_SDK = False
    logger.warning("google-antigravity SDK not found or incompatible. Loading functional emulation layer via google-genai...")
    
    # Define custom types and base classes for the emulation layer
    class HookResult:
        def __init__(self, allow: bool = True):
            self.allow = allow

    class QuestionHookResult:
        def __init__(self, responses: list = None):
            self.responses = responses or []

    class ToolCall:
        def __init__(self, name: str, args: dict):
            self.name = name
            self.args = args

    class LocalAgentConfig:
        def __init__(
            self,
            model: str = "gemini-2.5-flash",
            system_instructions: str = "",
            tools: list = None,
            hooks: list = None,
            response_schema: Any = None,
            app_data_dir: str = ""
        ):
            self.model = model
            self.system_instructions = system_instructions
            self.tools = tools or []
            self.hooks = hooks or []
            self.response_schema = response_schema
            self.app_data_dir = app_data_dir

    # Simple mock hooks namespace
    class MockHooks:
        def __init__(self):
            self._on_tool_error_callbacks = []
            
        def on_tool_error(self, func: Callable):
            self._on_tool_error_callbacks.append(func)
            return func
            
    hooks = MockHooks()

    # Stub base classes for class-based hooks
    class OnToolErrorHook:
        async def run(self, context: Any, data: Exception) -> Optional[str]:
            return None

    class HookContext:
        def __init__(self, tool_name: str):
            self.tool_name = tool_name

    class AgentResponse:
        def __init__(self, text_content: str, thoughts_content: str = "", structured: Any = None):
            self._text = text_content
            self._thoughts = thoughts_content
            self._structured = structured
            
        async def text(self) -> str:
            return self._text
            
        async def structured_output(self) -> Any:
            return self._structured
            
        @property
        def thoughts(self) -> AsyncIterator[str]:
            async def gen():
                if self._thoughts:
                    yield self._thoughts
            return gen()
            
        def __aiter__(self):
            async def gen():
                yield self._text
            return gen()

    class Agent:
        def __init__(self, config: LocalAgentConfig):
            self.config = config
            self._client = None
            
        async def __aenter__(self):
            # Check for API key in env or .env file
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY environment variable not set!")
                raise ValueError("GEMINI_API_KEY environment variable is required to access Gemini models.")
            
            # Import google-genai inside enter to avoid failures if not installed
            from google import genai
            self._client = genai.Client(api_key=api_key)
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
        async def chat(self, prompt: str) -> AgentResponse:
            from google.genai import types as genai_types
            from backend.state import log_agent_action
            
            # 1. Map tools to their python signatures
            tool_map = {t.__name__: t for t in self.config.tools}
            
            # Prepare Gemini tool list
            gemini_tools = [{"function_declarations": []}]
            # Or pass list of function references directly in python-genai SDK
            gemini_tools = self.config.tools
            
            # Setup generation config
            gen_config = genai_types.GenerateContentConfig(
                system_instruction=self.config.system_instructions,
                tools=gemini_tools,
                temperature=0.2
            )
            
            # Add schema constraint if response_schema is defined
            if self.config.response_schema:
                gen_config.response_mime_type = "application/json"
                gen_config.response_schema = self.config.response_schema
                
            model_name = self.config.model
            # PyPI GenAI SDK requires specific model names
            if "pro" in model_name:
                model_name = "gemini-2.5-pro"
            else:
                model_name = "gemini-2.5-flash"
                
            logger.info(f"Sending prompt to Gemini ({model_name})...")
            
            # Call Gemini
            response = self._client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=gen_config
            )
            
            thoughts = ""
            # Capture model internal thought from candidate explanation if available
            if response.candidates and response.candidates[0].content:
                parts = response.candidates[0].content.parts
                for p in parts:
                    if getattr(p, "text", None):
                        logger.info(f"Model Thought/Text: {p.text}")
            
            # 2. Emulate tool calling loop
            max_turns = 5
            turn = 0
            while response.function_calls and turn < max_turns:
                turn += 1
                logger.info(f"Model requested tool calls (turn {turn}): {response.function_calls}")
                
                tool_responses = []
                for call in response.function_calls:
                    tool_name = call.name
                    args = call.args
                    
                    logger.info(f"Executing tool '{tool_name}' with args {args}...")
                    
                    tool_output = ""
                    error_occurred = False
                    
                    if tool_name in tool_map:
                        try:
                            # Run python tool
                            res = tool_map[tool_name](**args)
                            tool_output = str(res)
                            log_agent_action(
                                step=f"Tool Call: {tool_name}",
                                reasoning="Automatic response coordination",
                                tool_called=tool_name,
                                outcome=f"SUCCESS: {tool_output[:100]}..."
                            )
                        except Exception as e:
                            logger.error(f"Tool {tool_name} failed: {e}")
                            error_occurred = True
                            tool_output = f"Error executing tool {tool_name}: {str(e)}"
                            
                            # Execute on_tool_error hooks
                            fallback_val = None
                            
                            # First check config hooks list (class-based or instance-based)
                            for hook in self.config.hooks:
                                # Check class hook
                                if hasattr(hook, "run"):
                                    ctx = HookContext(tool_name=tool_name)
                                    fallback_val = await hook.run(ctx, e)
                                    if fallback_val:
                                        break
                                        
                            # Then check decorator-based hooks
                            if not fallback_val:
                                for callback in hooks._on_tool_error_callbacks:
                                    try:
                                        fallback_val = await callback(e)
                                        if fallback_val:
                                            break
                                    except Exception:
                                        pass
                                        
                            if fallback_val:
                                logger.info(f"Hook intercepted error. Self-correction feedback applied: {fallback_val}")
                                tool_output = fallback_val
                                log_agent_action(
                                    step=f"Tool Error Intercepted: {tool_name}",
                                    reasoning="Antigravity Hook self-correction",
                                    tool_called=tool_name,
                                    outcome=f"FALLBACK APPLIED: {fallback_val}"
                                )
                            else:
                                log_agent_action(
                                    step=f"Tool Call Failed: {tool_name}",
                                    reasoning="No recovery hook applied",
                                    tool_called=tool_name,
                                    outcome=f"ERROR: {str(e)}"
                                )
                    else:
                        tool_output = f"Error: Tool {tool_name} is not bound or supported."
                    
                    tool_responses.append(
                        genai_types.Part.from_function_response(
                            name=tool_name,
                            response={"result": tool_output}
                        )
                    )
                
                # Send tool execution outputs back to model to continue the loop
                response = self._client.models.generate_content(
                    model=model_name,
                    contents=[
                        # Maintain standard history/session
                        prompt,
                        # Send past candidate contents back along with tool responses
                        response.candidates[0].content,
                        # Map function response parts
                        genai_types.Content(role="user", parts=tool_responses)
                    ],
                    config=gen_config
                )
            
            # Extract final text
            final_text = response.text or ""
            
            # Map structured output if JSON is requested
            structured_data = None
            if self.config.response_schema:
                try:
                    structured_data = json.loads(final_text)
                except Exception:
                    pass
                    
            return AgentResponse(
                text_content=final_text,
                thoughts_content=thoughts or "Evaluating gate states and security alert status...",
                structured=structured_data
            )
