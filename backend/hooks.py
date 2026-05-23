from typing import Any, Optional

# Import hook base classes — use real SDK if installed, else emulation layer
try:
    from google.antigravity.hooks import OnToolErrorHook, HookContext
except ImportError:
    # Emulation layer fallback (local dev without real SDK)
    from backend.agent_wrapper import OnToolErrorHook, HookContext

class FallbackHook(OnToolErrorHook):
    """Intercepts tool execution errors and returns targeted recovery guidance."""

    async def run(self, context: HookContext, data: Exception) -> Optional[str]:
        # Extract the failed tool name
        tool_name = getattr(context, "tool_name", "unknown")
        
        # Standardize an explicit self-correction warning that guides the model
        feedback = (
            f"[SYSTEM SELF-CORRECTION ALERT]: The tool '{tool_name}' raised a runtime error "
            f"during execution: {str(data)}. "
            f"Action required: Autonomously modify the inputs (e.g. ensure the gate ID or "
            f"location parameters match valid stadium designations) and re-try calling the "
            f"appropriate tool with corrected values."
        )
        
        return feedback
