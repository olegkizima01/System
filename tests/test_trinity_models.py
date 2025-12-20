"""Unit tests for Trinity graph nodes."""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import after mocking if needed
from core.trinity_models import (
    TrinityStateModel, MetaConfig, TaskType, ExecutionMode, GuiMode, StepStatus
)


class TestMetaConfigModel:
    """Test MetaConfig Pydantic model."""

    def test_meta_config_defaults(self):
        """Test that MetaConfig has proper defaults."""
        config = MetaConfig()
        assert config.strategy == "hybrid"
        assert config.verification_rigor == "standard"
        assert config.recovery_mode == "local_fix"
        assert config.tool_preference == "hybrid"
        assert config.reasoning == ""
        assert config.n_results == 3

    def test_meta_config_validation_strategy(self):
        """Test strategy validation."""
        with pytest.raises(ValueError):
            MetaConfig(strategy="invalid_strategy")
        
        # Valid strategies should work
        config = MetaConfig(strategy="linear")
        assert config.strategy == "linear"
        
        config = MetaConfig(strategy="rag_heavy")
        assert config.strategy == "rag_heavy"

    def test_meta_config_validation_rigor(self):
        """Test verification_rigor validation."""
        with pytest.raises(ValueError):
            MetaConfig(verification_rigor="invalid_rigor")
        
        valid_rigors = ["low", "standard", "high", "strict"]
        for rigor in valid_rigors:
            config = MetaConfig(verification_rigor=rigor)
            assert config.verification_rigor == rigor

    def test_meta_config_n_results_bounds(self):
        """Test n_results bounds validation."""
        # Should accept valid range
        config = MetaConfig(n_results=5)
        assert config.n_results == 5
        
        # Should reject out of bounds
        with pytest.raises(ValueError):
            MetaConfig(n_results=0)
        
        with pytest.raises(ValueError):
            MetaConfig(n_results=11)


class TestTrinityStateModel:
    """Test TrinityStateModel Pydantic model."""

    def test_trinity_state_defaults(self):
        """Test that TrinityStateModel has proper defaults."""
        state = TrinityStateModel()
        
        assert state.current_agent == "meta_planner"
        assert state.task_status == "started"
        assert state.step_count == 0
        assert state.replan_count == 0
        assert state.plan == []
        assert state.is_dev == False
        assert state.gui_mode == GuiMode.AUTO
        assert state.execution_mode == ExecutionMode.NATIVE
        assert isinstance(state.meta_config, MetaConfig)

    def test_trinity_state_creation_from_dict(self):
        """Test creating state from dictionary."""
        data = {
            "current_agent": "atlas",
            "task_type": "DEV",
            "is_dev": True,
            "step_count": 5,
            "plan": [{"description": "Step 1"}],
            "meta_config": {
                "strategy": "linear",
                "verification_rigor": "high"
            }
        }
        
        state = TrinityStateModel.from_dict(data)
        assert state.current_agent == "atlas"
        assert state.task_type == TaskType.DEV
        assert state.is_dev == True
        assert state.step_count == 5
        assert len(state.plan) == 1
        assert state.meta_config.strategy == "linear"
        assert state.meta_config.verification_rigor == "high"

    def test_trinity_state_validation(self):
        """Test state validation."""
        state = TrinityStateModel()
        assert state.validate_state() == True
        
        # Invalid agent should fail
        state.current_agent = "invalid_agent"
        with pytest.raises(ValueError):
            state.validate_state()

    def test_trinity_state_to_dict(self):
        """Test converting state to dict."""
        state = TrinityStateModel(
            current_agent="atlas",
            step_count=3,
            is_dev=True
        )
        
        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict["current_agent"] == "atlas"
        assert state_dict["step_count"] == 3
        assert state_dict["is_dev"] == True

    def test_trinity_state_negative_counts_rejected(self):
        """Test that negative step/replan counts are rejected."""
        with pytest.raises(ValueError):
            TrinityStateModel(step_count=-1)
        
        with pytest.raises(ValueError):
            TrinityStateModel(replan_count=-1)


class TestStateInitialization:
    """Test proper state initialization for Trinity graph."""

    def test_initial_state_for_dev_task(self):
        """Test initial state creation for a DEV task."""
        task = "Write a Python function"
        
        state_data = {
            "messages": [{"content": task}],
            "current_agent": "meta_planner",
            "task_type": "DEV",
            "is_dev": True,
            "requires_windsurf": False,
            "execution_mode": "native",
            "gui_mode": "auto",
            "meta_config": {
                "strategy": "hybrid",
                "verification_rigor": "standard",
                "recovery_mode": "local_fix",
                "tool_preference": "hybrid",
                "reasoning": "",
                "retrieval_query": task[:100],
                "n_results": 3
            },
            "retrieved_context": "",
            "original_task": task,
            "is_media": False,
        }
        
        state = TrinityStateModel.from_dict(state_data)
        assert state.is_dev == True
        assert state.task_type == TaskType.DEV
        assert state.requires_windsurf == False
        assert state.meta_config.strategy == "hybrid"
        assert state.retrieved_context == ""

    def test_initial_state_has_all_required_fields(self):
        """Test that initial state has all required fields."""
        state = TrinityStateModel()
        
        # Check critical fields
        assert hasattr(state, 'messages')
        assert hasattr(state, 'current_agent')
        assert hasattr(state, 'meta_config')
        assert hasattr(state, 'plan')
        assert hasattr(state, 'step_count')
        assert hasattr(state, 'meta_config')
        
        # Check that meta_config has required keys
        assert hasattr(state.meta_config, 'strategy')
        assert hasattr(state.meta_config, 'verification_rigor')
        assert hasattr(state.meta_config, 'recovery_mode')
        assert hasattr(state.meta_config, 'tool_preference')
        assert hasattr(state.meta_config, 'reasoning')
        assert hasattr(state.meta_config, 'retrieval_query')
        assert hasattr(state.meta_config, 'n_results')


class TestStateTransitions:
    """Test valid state transitions in Trinity graph."""

    def test_transition_from_meta_planner_to_atlas(self):
        """Test transition from meta_planner to atlas."""
        state = TrinityStateModel(
            current_agent="meta_planner",
            step_count=0
        )
        
        # Should be able to transition to atlas
        state.current_agent = "atlas"
        state.step_count = 1
        assert state.validate_state() == True

    def test_transition_chain(self):
        """Test a chain of valid transitions."""
        transitions = [
            ("meta_planner", 0),
            ("atlas", 1),
            ("tetyana", 2),
            ("grisha", 3),
            ("meta_planner", 4),
            ("end", 4)
        ]
        
        state = TrinityStateModel()
        for agent, step in transitions:
            state.current_agent = agent
            state.step_count = step
            assert state.validate_state() == True

    def test_invalid_transition_rejects(self):
        """Test that invalid agents are rejected."""
        state = TrinityStateModel()
        state.current_agent = "nonexistent_agent"
        
        with pytest.raises(ValueError):
            state.validate_state()


class TestMetaConfigUpdate:
    """Test meta_config updates during execution."""

    def test_meta_config_update_preserves_all_fields(self):
        """Test that updating meta_config preserves all fields."""
        config = MetaConfig(
            strategy="linear",
            verification_rigor="high",
            n_results=5
        )
        
        # Simulate an update
        updated_config = MetaConfig(
            strategy="rag_heavy",
            verification_rigor=config.verification_rigor,
            n_results=config.n_results,
            reasoning="Updated strategy"
        )
        
        assert updated_config.strategy == "rag_heavy"
        assert updated_config.verification_rigor == "high"
        assert updated_config.n_results == 5
        assert updated_config.reasoning == "Updated strategy"

    def test_meta_config_setdefault_pattern(self):
        """Test the setdefault pattern used in trinity.py."""
        config_dict = {"strategy": "linear"}
        config = MetaConfig(**config_dict)
        
        # Simulate the setdefault pattern
        if not config.reasoning:
            config.reasoning = ""
        if not config.retrieval_query:
            config.retrieval_query = "test query"
        
        assert config.reasoning == ""
        assert config.retrieval_query == "test query"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
