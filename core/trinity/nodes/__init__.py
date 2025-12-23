"""
Trinity Node implementations - Agent graph nodes.

This package contains the individual agent node implementations
for the Trinity runtime graph.
"""

from core.trinity.nodes.base import NodeResult, extract_last_message

__all__ = [
    "NodeResult",
    "extract_last_message",
]
