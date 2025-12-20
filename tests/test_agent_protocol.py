"""Tests for Agent Message Protocol."""

import pytest
import time
from core.agent_protocol import (
    AgentMessage,
    MessageType,
    MessageRouter,
    PriorityMessageQueue,
    get_message_router,
    request_plan,
    request_execution,
    report_error
)


class TestAgentMessage:
    """Tests for AgentMessage dataclass."""

    def test_create_message(self):
        """Test basic message creation."""
        msg = AgentMessage(
            sender="atlas",
            receiver="tetyana",
            message_type=MessageType.REQUEST,
            content={"action": "execute"}
        )
        
        assert msg.sender == "atlas"
        assert msg.receiver == "tetyana"
        assert msg.message_type == MessageType.REQUEST
        assert msg.correlation_id is not None

    def test_to_dict(self):
        """Test message serialization."""
        msg = AgentMessage(
            sender="grisha",
            receiver="meta_planner",
            message_type=MessageType.RESPONSE,
            content={"status": "verified"},
            priority=8
        )
        
        data = msg.to_dict()
        
        assert data["sender"] == "grisha"
        assert data["message_type"] == "response"
        assert data["priority"] == 8

    def test_from_dict(self):
        """Test message deserialization."""
        data = {
            "sender": "atlas",
            "receiver": "tetyana",
            "message_type": "request",
            "content": {"task": "test"},
            "priority": 5
        }
        
        msg = AgentMessage.from_dict(data)
        
        assert msg.sender == "atlas"
        assert msg.message_type == MessageType.REQUEST

    def test_create_response(self):
        """Test response message creation."""
        original = AgentMessage(
            sender="meta_planner",
            receiver="atlas",
            message_type=MessageType.REQUEST,
            content={"action": "plan"}
        )
        
        response = original.create_response(
            sender="atlas",
            content={"plan": ["step1", "step2"]}
        )
        
        assert response.sender == "atlas"
        assert response.receiver == "meta_planner"
        assert response.message_type == MessageType.RESPONSE
        assert response.correlation_id == original.correlation_id


class TestPriorityMessageQueue:
    """Tests for PriorityMessageQueue."""

    def test_priority_ordering(self):
        """Test messages are returned in priority order."""
        q = PriorityMessageQueue()
        
        # Add messages with different priorities
        low = AgentMessage("atlas", "tetyana", MessageType.REQUEST, {}, priority=1)
        high = AgentMessage("atlas", "tetyana", MessageType.REQUEST, {}, priority=9)
        med = AgentMessage("atlas", "tetyana", MessageType.REQUEST, {}, priority=5)
        
        q.put(low)
        q.put(high)
        q.put(med)
        
        # Should get high priority first
        first = q.get()
        assert first.priority == 9
        
        second = q.get()
        assert second.priority == 5
        
        third = q.get()
        assert third.priority == 1

    def test_fifo_same_priority(self):
        """Test FIFO ordering for same priority."""
        q = PriorityMessageQueue()
        
        msg1 = AgentMessage("a", "b", MessageType.REQUEST, {"id": 1}, priority=5)
        msg2 = AgentMessage("a", "b", MessageType.REQUEST, {"id": 2}, priority=5)
        
        q.put(msg1)
        q.put(msg2)
        
        first = q.get()
        assert first.content["id"] == 1

    def test_empty_queue(self):
        """Test empty queue behavior."""
        q = PriorityMessageQueue()
        
        assert q.empty()
        assert q.get(timeout=0.1) is None


class TestMessageRouter:
    """Tests for MessageRouter."""

    def test_subscribe_and_send_direct(self):
        """Test subscription and direct message sending."""
        router = MessageRouter()
        received = []
        
        def handler(msg):
            received.append(msg)
        
        router.subscribe("tetyana", handler)
        
        msg = AgentMessage(
            sender="atlas",
            receiver="tetyana",
            message_type=MessageType.REQUEST,
            content={"task": "test"}
        )
        
        router.send_direct(msg)
        
        assert len(received) == 1
        assert received[0].content["task"] == "test"

    def test_broadcast(self):
        """Test broadcast message delivery."""
        router = MessageRouter()
        received_count = [0]  # Use list for mutability in closure
        
        def handler(msg):
            received_count[0] += 1
        
        router.subscribe("all", handler)
        
        router.broadcast(
            sender="meta_planner",
            content={"event": "task_started"}
        )
        
        router.process_pending()
        
        assert received_count[0] >= 1

    def test_history(self):
        """Test message history tracking."""
        router = MessageRouter()
        
        msg1 = AgentMessage("atlas", "tetyana", MessageType.REQUEST, {"id": 1})
        msg2 = AgentMessage("tetyana", "grisha", MessageType.RESPONSE, {"id": 2})
        
        router.send_direct(msg1)
        router.send_direct(msg2)
        
        history = router.get_history()
        
        assert len(history) == 2

    def test_history_filter_by_agent(self):
        """Test history filtering by agent."""
        router = MessageRouter()
        
        router.send_direct(AgentMessage("atlas", "tetyana", MessageType.REQUEST, {}))
        router.send_direct(AgentMessage("grisha", "meta_planner", MessageType.RESPONSE, {}))
        
        atlas_history = router.get_history(agent="atlas")
        
        assert len(atlas_history) == 1
        assert atlas_history[0]["sender"] == "atlas"

    def test_stats(self):
        """Test router statistics."""
        router = MessageRouter()
        router.subscribe("test_agent", lambda m: None)
        
        router.send_direct(AgentMessage("a", "b", MessageType.REQUEST, {}))
        
        stats = router.get_stats()
        
        assert "test_agent" in stats["subscribed_agents"]
        assert stats["history_size"] >= 1


class TestConvenienceFunctions:
    """Tests for convenience message creation functions."""

    def test_request_plan(self):
        """Test plan request message creation."""
        msg = request_plan("meta_planner", "Open Chrome browser")
        
        assert msg.sender == "meta_planner"
        assert msg.receiver == "atlas"
        assert msg.content["action"] == "generate_plan"
        assert msg.priority == 7

    def test_request_execution(self):
        """Test execution request message creation."""
        step = {"id": 1, "tool": "open_app", "args": {"name": "Chrome"}}
        msg = request_execution("atlas", step)
        
        assert msg.receiver == "tetyana"
        assert msg.content["step"] == step

    def test_report_error(self):
        """Test error report message creation."""
        msg = report_error("tetyana", "Tool execution failed")
        
        assert msg.receiver == "meta_planner"
        assert msg.message_type == MessageType.ERROR
        assert msg.priority == 9  # High priority for errors
