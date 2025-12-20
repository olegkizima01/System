"""Agent Message Protocol

Formalized inter-agent communication protocol for Trinity Runtime.
Provides traceable, priority-based message routing between agents.

Features:
- Typed agent messages with priority
- Message routing and subscription
- Event-driven architecture support
- Message history for debugging
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional
from enum import Enum
import threading
import queue
import time


class MessageType(Enum):
    """Types of messages between agents."""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    ERROR = "error"
    STATUS = "status"
    COMMAND = "command"


AgentName = Literal["meta_planner", "atlas", "tetyana", "grisha", "knowledge", "context7", "system"]


@dataclass
class AgentMessage:
    """
    Structured message for inter-agent communication.
    
    Attributes:
        sender: Name of the sending agent
        receiver: Name of the receiving agent (or "all" for broadcast)
        message_type: Type of message
        content: Message payload
        priority: Priority level (0-10, higher = more important)
        correlation_id: ID to correlate request/response pairs
        timestamp: When the message was created
        metadata: Additional metadata
    """
    sender: AgentName
    receiver: str  # AgentName or "all"
    message_type: MessageType
    content: Dict[str, Any]
    priority: int = 5
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.correlation_id is None:
            self.correlation_id = f"msg_{int(time.time() * 1000)}_{self.sender}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "content": self.content,
            "priority": self.priority,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create from dictionary."""
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            priority=data.get("priority", 5),
            correlation_id=data.get("correlation_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            metadata=data.get("metadata", {})
        )
    
    def create_response(
        self,
        sender: AgentName,
        content: Dict[str, Any],
        priority: Optional[int] = None
    ) -> "AgentMessage":
        """Create a response message to this message."""
        return AgentMessage(
            sender=sender,
            receiver=self.sender,
            message_type=MessageType.RESPONSE,
            content=content,
            priority=priority if priority is not None else self.priority,
            correlation_id=self.correlation_id,
            metadata={"in_response_to": self.correlation_id}
        )


class PriorityMessageQueue:
    """Thread-safe priority queue for agent messages."""
    
    def __init__(self, maxsize: int = 1000):
        self._queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=maxsize)
        self._counter = 0
        self._lock = threading.Lock()
    
    def put(self, message: AgentMessage) -> None:
        """Add message to queue (higher priority = processed first)."""
        with self._lock:
            # Negative priority so higher values come first
            # Counter ensures FIFO for same priority
            priority_tuple = (-message.priority, self._counter, message)
            self._counter += 1
            self._queue.put(priority_tuple)
    
    def get(self, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Get next message from queue."""
        try:
            _, _, message = self._queue.get(timeout=timeout)
            return message
        except queue.Empty:
            return None
    
    def empty(self) -> bool:
        return self._queue.empty()
    
    def qsize(self) -> int:
        return self._queue.qsize()


MessageHandler = Callable[[AgentMessage], Optional[AgentMessage]]


class MessageRouter:
    """
    Routes messages between Trinity agents.
    
    Features:
    - Subscribe agents to receive messages
    - Priority-based message queue
    - Broadcast support
    - Message history for debugging
    """
    
    MAX_HISTORY = 500
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._handlers: Dict[str, List[MessageHandler]] = {}
        self._message_queue = PriorityMessageQueue()
        self._history: List[AgentMessage] = []
        self._history_lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
    
    def subscribe(self, agent: str, handler: MessageHandler) -> None:
        """
        Subscribe an agent to receive messages.
        
        Args:
            agent: Agent name (or "all" for all messages)
            handler: Callback function to handle messages
        """
        if agent not in self._handlers:
            self._handlers[agent] = []
        self._handlers[agent].append(handler)
        
        if self.verbose:
            print(f"[MessageRouter] {agent} subscribed")
    
    def unsubscribe(self, agent: str, handler: Optional[MessageHandler] = None) -> None:
        """
        Unsubscribe agent from messages.
        
        Args:
            agent: Agent name
            handler: Specific handler to remove (or None to remove all)
        """
        if agent in self._handlers:
            if handler:
                self._handlers[agent] = [h for h in self._handlers[agent] if h != handler]
            else:
                del self._handlers[agent]
    
    def send(self, message: AgentMessage) -> None:
        """
        Send a message to the queue.
        
        Args:
            message: Message to send
        """
        self._message_queue.put(message)
        self._record_history(message)
        
        if self.verbose:
            print(f"[MessageRouter] {message.sender} -> {message.receiver}: {message.message_type.value}")
    
    def send_direct(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Send message directly (synchronous, bypasses queue).
        
        Returns response if handler returns one.
        """
        self._record_history(message)
        return self._dispatch(message)
    
    def broadcast(
        self,
        sender: AgentName,
        content: Dict[str, Any],
        priority: int = 5
    ) -> None:
        """
        Broadcast message to all agents.
        """
        message = AgentMessage(
            sender=sender,
            receiver="all",
            message_type=MessageType.BROADCAST,
            content=content,
            priority=priority
        )
        self.send(message)
    
    def _dispatch(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Dispatch message to appropriate handlers."""
        response = None
        
        # Find handlers for this message
        handlers = []
        
        # Direct handlers for the receiver
        if message.receiver in self._handlers:
            handlers.extend(self._handlers[message.receiver])
        
        # Broadcast handlers (subscribed to "all")
        if "all" in self._handlers:
            handlers.extend(self._handlers["all"])
        
        # Execute handlers
        for handler in handlers:
            try:
                result = handler(message)
                if result is not None and response is None:
                    response = result
            except Exception as e:
                if self.verbose:
                    print(f"[MessageRouter] Handler error: {e}")
        
        return response
    
    def _record_history(self, message: AgentMessage) -> None:
        """Record message in history."""
        with self._history_lock:
            self._history.append(message)
            if len(self._history) > self.MAX_HISTORY:
                self._history = self._history[-self.MAX_HISTORY:]
    
    def get_history(
        self,
        agent: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get message history with optional filtering.
        
        Args:
            agent: Filter by sender or receiver
            message_type: Filter by message type
            limit: Max messages to return
        """
        with self._history_lock:
            filtered = self._history.copy()
        
        if agent:
            filtered = [
                m for m in filtered 
                if m.sender == agent or m.receiver == agent
            ]
        
        if message_type:
            filtered = [m for m in filtered if m.message_type == message_type]
        
        return [m.to_dict() for m in filtered[-limit:]]
    
    def start_async_processing(self) -> None:
        """Start background thread for async message processing."""
        if self._running:
            return
            
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._worker_thread.start()
        
        if self.verbose:
            print("[MessageRouter] Async processing started")
    
    def stop_async_processing(self) -> None:
        """Stop background processing."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=2)
    
    def _process_loop(self) -> None:
        """Background processing loop."""
        while self._running:
            message = self._message_queue.get(timeout=0.1)
            if message:
                self._dispatch(message)
    
    def process_pending(self) -> int:
        """
        Process all pending messages synchronously.
        
        Returns number of messages processed.
        """
        count = 0
        while not self._message_queue.empty():
            message = self._message_queue.get(timeout=0)
            if message:
                self._dispatch(message)
                count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        with self._history_lock:
            history_count = len(self._history)
            
            # Count by type
            type_counts = {}
            for msg in self._history:
                t = msg.message_type.value
                type_counts[t] = type_counts.get(t, 0) + 1
            
            # Count by agent
            agent_counts = {}
            for msg in self._history:
                agent_counts[msg.sender] = agent_counts.get(msg.sender, 0) + 1
        
        return {
            "subscribed_agents": list(self._handlers.keys()),
            "queue_size": self._message_queue.qsize(),
            "history_size": history_count,
            "messages_by_type": type_counts,
            "messages_by_agent": agent_counts,
            "async_running": self._running
        }


# Convenience functions for common message patterns
def request_plan(sender: AgentName, task: str, context: Dict[str, Any] = None) -> AgentMessage:
    """Create a planning request message."""
    return AgentMessage(
        sender=sender,
        receiver="atlas",
        message_type=MessageType.REQUEST,
        content={"action": "generate_plan", "task": task, "context": context or {}},
        priority=7
    )


def request_execution(sender: AgentName, step: Dict[str, Any]) -> AgentMessage:
    """Create an execution request message."""
    return AgentMessage(
        sender=sender,
        receiver="tetyana",
        message_type=MessageType.REQUEST,
        content={"action": "execute_step", "step": step},
        priority=8
    )


def request_verification(sender: AgentName, result: Dict[str, Any]) -> AgentMessage:
    """Create a verification request message."""
    return AgentMessage(
        sender=sender,
        receiver="grisha",
        message_type=MessageType.REQUEST,
        content={"action": "verify_result", "result": result},
        priority=6
    )


def report_error(sender: AgentName, error: str, context: Dict[str, Any] = None) -> AgentMessage:
    """Create an error report message."""
    return AgentMessage(
        sender=sender,
        receiver="meta_planner",
        message_type=MessageType.ERROR,
        content={"error": error, "context": context or {}},
        priority=9
    )


# Global router instance
_router_instance: Optional[MessageRouter] = None


def get_message_router() -> MessageRouter:
    """Get the global message router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = MessageRouter(verbose=False)
    return _router_instance
