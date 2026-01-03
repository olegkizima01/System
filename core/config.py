import os
import yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ValidationError
from pathlib import Path

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    file_path: str = "logs/trinity_state.log"
    console_output: bool = True

class MCPServerConfig(BaseModel):
    enabled: bool = True
    command: str
    args: List[str] =Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)

class MCPConfig(BaseModel):
    mode: str = "dynamic"
    global_binary_fallback: bool = True
    servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)

class VisionConfig(BaseModel):
    enabled: bool = True
    multi_monitor: bool = True
    diff_analysis: bool = True

class AgentConfig(BaseModel):
    default_timeout: int = 300
    max_retries: int = 3
    vision: VisionConfig = Field(default_factory=VisionConfig)

class PathConfig(BaseModel):
    artifacts_dir: str = ".agent/artifacts"
    memory_dir: str = ".agent/memory"

class Settings(BaseModel):
    app_name: str = "Atlas"
    version: str = "2.5.0"
    env: str = "development"
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    paths: PathConfig = Field(default_factory=PathConfig)

class ConfigLoader:
    _instance = None
    _settings: Optional[Settings] = None

    @classmethod
    def load(cls, config_path: str = "config/settings.yaml") -> Settings:
        if cls._settings:
            return cls._settings

        path = Path(config_path)
        if not path.exists():
            # Fallback or raise error? For now, nice fallback
            return Settings()
        
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            
            # Flatten 'settings' key if present (legacy mismatch fix)
            if "settings" in data and isinstance(data["settings"], dict):
                nested = data.pop("settings")
                data.update(nested)
            
            cls._settings = Settings(**data)
            return cls._settings
        except Exception as e:
            print(f"Error loading config: {e}")
            raise

    @classmethod
    def get_settings(cls) -> Settings:
        if cls._settings is None:
            return cls.load()
        return cls._settings

# Global accessor
settings = ConfigLoader.get_settings()
