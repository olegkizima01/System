from core.trinity import TrinityRuntime
from langchain_core.messages import AIMessage

class _DummyWorkflow:
    def stream(self, initial_state, config=None):
        yield {"atlas": {"messages": [AIMessage(content="ok")], "current_agent": "tetyana", "plan": [{"description": "Edit file", "type": "execute", "tools": [{"name": "write_file", "args": {"path": "some_change.txt", "content": "y"}}]}]}}

rt = TrinityRuntime(verbose=True)
rt.workflow = _DummyWorkflow()
for e in rt.run("Make dev change"):
    print("EVENT:", e)
print("DONE")
