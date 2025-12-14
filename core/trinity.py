from typing import Annotated, TypedDict, Literal, List, Dict, Any, Optional
import json
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from core.agents.atlas import get_atlas_prompt
from core.agents.tetyana import get_tetyana_prompt
from core.agents.grisha import get_grisha_prompt
from providers.copilot import CopilotLLM

# Import Tools
from system_ai.tools.executor import run_shell, open_app, run_applescript
from system_ai.tools.screenshot import take_screenshot

# Define the state of the Trinity system
class TrinityState(TypedDict):
    messages: List[BaseMessage]
    current_agent: str
    task_status: str
    final_response: Optional[str]

class TrinityRuntime:
    def __init__(self, verbose: bool = True):
        self.llm = CopilotLLM()
        self.verbose = verbose
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(TrinityState)

        workflow.add_node("atlas", self._atlas_node)
        workflow.add_node("tetyana", self._tetyana_node)
        workflow.add_node("grisha", self._grisha_node)

        workflow.set_entry_point("atlas")
        
        workflow.add_conditional_edges(
            "atlas", 
            self._router, 
            {"tetyana": "tetyana", "grisha": "grisha", "end": END}
        )
        workflow.add_conditional_edges(
            "tetyana", 
            self._router, 
            {"grisha": "grisha", "atlas": "atlas", "end": END}
        )
        workflow.add_conditional_edges(
            "grisha", 
            self._router, 
            {"atlas": "atlas", "end": END}
        )

        return workflow.compile()

    def _atlas_node(self, state: TrinityState):
        if self.verbose: print("🌐 [Atlas] Strategizing...")
        context = state.get("messages", [])
        last_msg = context[-1].content if context else "Start"
        
        # Invoke Atlas Persona
        prompt = get_atlas_prompt(last_msg)
        try:
            response = self.llm.invoke(prompt.format_messages())
            content = response.content
        except Exception as e:
            content = f"Error invoking Atlas: {e}"
            return {"current_agent": "end", "messages": [AIMessage(content=content)]}

        # Simple heuristic router based on content (Real reasoning would need structured output)
        next_agent = "tetyana" if "tetyana" in content.lower() else "grisha" if "grisha" in content.lower() else "end"
        
        # Use a default next step if Atlas is vague
        if next_agent == "end" and "plan" in content.lower():
            next_agent = "tetyana"

        return {"current_agent": next_agent, "messages": [AIMessage(content=content)]}

    def _tetyana_node(self, state: TrinityState):
        if self.verbose: print("💻 [Tetyana] Developing...")
        context = state.get("messages", [])
        last_msg = context[-1].content
        
        prompt = get_tetyana_prompt(last_msg)
        try:
            response = self.llm.invoke(prompt.format_messages())
            # For now, we assume direct text or basic JSON. 
            # In a full impl, we'd use tool usage parsing as seen in CopilotLLM.
            content = response.content
            tool_calls = response.tool_calls if hasattr(response, 'tool_calls') else []
            
            # If no structured tool calls, try to parse JSON manually or via simple heuristics
            # (Assuming CopilotLLM returns tool_calls formatted)
            
            results = []
            if tool_calls:
                 for tool in tool_calls:
                     name = tool.get("name")
                     args = tool.get("args") or {}
                     if name == "run_shell":
                         res = run_shell(args.get("command"), allow=True)
                         results.append(f"Result for {name}: {res}")
                     elif name == "open_app":
                         res = open_app(args.get("name"))
                         results.append(f"Result for {name}: {res}")
                     # Add other mappings
            
            # If we executed tools, append results to content
            if results:
                content += "\n\nTool Results:\n" + "\n".join(results)
                
        except Exception as e:
            content = f"Error invoking Tetyana: {e}"
        
        return {
            "current_agent": "grisha", 
            "messages": [AIMessage(content=content)]
        }

    def _grisha_node(self, state: TrinityState):
        if self.verbose: print("👁️ [Grisha] Verifying...")
        context = state.get("messages", [])
        last_msg = context[-1].content
        
        prompt = get_grisha_prompt(last_msg)
        try:
            response = self.llm.invoke(prompt.format_messages())
            content = response.content
        except Exception as e:
            content = f"Error invoking Grisha: {e}"

        # If Grisha says "CONFIRMED" or "VERIFIED", we end. Else Atlas replans.
        next_agent = "end" if "verified" in content.lower() or "confirmed" in content.lower() else "atlas"

        return {
            "current_agent": next_agent, 
            "messages": [AIMessage(content=content)]
        }

    def _router(self, state: TrinityState):
        return state["current_agent"]

    def run(self, input_text: str):
        initial_state = {
            "messages": [HumanMessage(content=input_text)],
            "current_agent": "atlas",
            "task_status": "started",
            "final_response": None
        }
        
        for event in self.workflow.stream(initial_state):
            yield event



