from typing import Any, Dict, Optional, Callable
import os
from core.mcp_registry import MCPToolRegistry

class TrinityToolsMixin:
    """Mixin for TrinityRuntime containing tool registration and management logic."""
    
    def _register_tools(self) -> None:
        """Register all local tools and MCP tools."""
        # Note: self.registry is expected to be initialized in TrinityRuntime.__init__
        
        from system_ai.tools.screenshot import get_frontmost_app, get_all_windows

        disable_vision = str(os.environ.get("TRINITY_DISABLE_VISION", "")).strip().lower() in {"1", "true", "yes", "on"}
        EnhancedVisionTools = None
        if not disable_vision:
            try:
                from system_ai.tools.vision import EnhancedVisionTools as _EnhancedVisionTools
                EnhancedVisionTools = _EnhancedVisionTools
            except Exception as e:
                # self.logger is expected to be available
                if hasattr(self, 'verbose') and self.verbose and hasattr(self, 'logger'):
                    self.logger.warning(f"Vision tools unavailable: {e}")
        
        # Core Vision Tools (optional)
        if EnhancedVisionTools is not None:
            self.registry.register_tool(
                "enhanced_vision_analysis",
                EnhancedVisionTools.capture_and_analyze,
                description="Capture screen and perform differential visual/OCR analysis. Args: app_name (optional), window_title (optional)"
            )

            self.registry.register_tool(
                "vision_analysis_with_context",
                lambda args: EnhancedVisionTools.analyze_with_context(
                    args.get("image_path"),
                    getattr(self, 'vision_context_manager', None)
                ),
                description="Analyze image and update global visual context"
            )
        
        # Window detection utilities
        self.registry.register_tool(
            "get_frontmost_app",
            lambda args: get_frontmost_app(),
            description="Get the currently active (frontmost) application name and window title on macOS"
        )
        
        self.registry.register_tool(
            "get_all_windows",
            lambda args: get_all_windows(),
            description="Get list of all visible windows with their app names, titles, positions and sizes"
        )
