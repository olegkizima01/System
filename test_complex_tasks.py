#!/usr/bin/env python3
"""
Complex Task Testing for Trinity Runtime
Tests various real-world scenarios to identify issues and improvements
"""

import os
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from core.trinity import TrinityRuntime, TrinityPermissions
from core.trinity.state import create_initial_state
from core.mcp_registry import MCPToolRegistry

def create_mock_llm():
    """Create a sophisticated mock LLM that handles different scenarios"""
    mock_llm = MagicMock()
    
    def smart_invoke(messages):
        """Intelligent mock that responds based on context"""
        if not messages:
            return MagicMock(content='{"error": "No messages provided"}')
        
        content = str(messages[-1].content if hasattr(messages[-1], 'content') else messages[-1])
        content_lower = content.lower()
        
        # Meta-Planner responses
        if any(keyword in content_lower for keyword in ['analyzing strategy', 'meta-planner', 'strategy']):
            return MagicMock(content='''{
                "meta_config": {
                    "strategy": "hybrid",
                    "verification_rigor": "standard",
                    "recovery_mode": "local_fix",
                    "tool_preference": "hybrid",
                    "reasoning": "Using hybrid approach for balanced performance and reliability"
                }
            }''')
        
        # Atlas (Planner) responses
        elif any(keyword in content_lower for keyword in ['generating steps', 'atlas', 'plan']):
            # Different plans for different task types
            if 'calculator' in content_lower:
                return MagicMock(content='''{
                    "steps": [
                        {
                            "id": 1,
                            "description": "Open Calculator application",
                            "agent": "tetyana",
                            "tools": ["open_app"],
                            "expected_result": "Calculator app launched"
                        },
                        {
                            "id": 2,
                            "description": "Verify calculator is open and responsive",
                            "agent": "grisha",
                            "tools": ["get_open_windows"],
                            "expected_result": "Calculator window detected"
                        }
                    ]
                }''')
            
            elif 'browser' in content_lower or 'google' in content_lower:
                return MagicMock(content='''{
                    "steps": [
                        {
                            "id": 1,
                            "description": "Open browser and navigate to Google",
                            "agent": "tetyana",
                            "tools": ["browser_open_url"],
                            "expected_result": "Browser opened with Google homepage"
                        },
                        {
                            "id": 2,
                            "description": "Search for requested information",
                            "agent": "tetyana",
                            "tools": ["browser_type_text", "browser_press_key"],
                            "expected_result": "Search results displayed"
                        },
                        {
                            "id": 3,
                            "description": "Verify search results are relevant",
                            "agent": "grisha",
                            "tools": ["browser_get_content", "vision_analyze"],
                            "expected_result": "Relevant search results confirmed"
                        }
                    ]
                }''')
            
            elif 'file' in content_lower or 'create' in content_lower:
                return MagicMock(content='''{
                    "steps": [
                        {
                            "id": 1,
                            "description": "Create new file with specified content",
                            "agent": "tetyana",
                            "tools": ["write_file"],
                            "expected_result": "File created successfully"
                        },
                        {
                            "id": 2,
                            "description": "Verify file exists and has correct content",
                            "agent": "grisha",
                            "tools": ["read_file"],
                            "expected_result": "File content verified"
                        }
                    ]
                }''')
            
            else:
                # Generic fallback plan
                return MagicMock(content='''{
                    "steps": [
                        {
                            "id": 1,
                            "description": "Execute the requested task",
                            "agent": "tetyana",
                            "tools": ["run_shell"],
                            "expected_result": "Task executed"
                        },
                        {
                            "id": 2,
                            "description": "Verify task completion",
                            "agent": "grisha",
                            "tools": ["get_system_stats"],
                            "expected_result": "Task verified"
                        }
                    ]
                }''')
        
        # Tetyana (Executor) responses
        elif any(keyword in content_lower for keyword in ['executing step', 'tetyana', 'execute']):
            if 'calculator' in content_lower:
                return MagicMock(content='''{
                    "tool_calls": [
                        {
                            "name": "open_app",
                            "args": {
                                "name": "Calculator"
                            }
                        }
                    ],
                    "execution_report": "Calculator application opened successfully"
                }''')
            
            elif 'browser' in content_lower:
                return MagicMock(content='''{
                    "tool_calls": [
                        {
                            "name": "browser_open_url",
                            "args": {
                                "url": "https://www.google.com"
                            }
                        }
                    ],
                    "execution_report": "Browser opened and navigated to Google"
                }''')
            
            elif 'file' in content_lower:
                return MagicMock(content='''{
                    "tool_calls": [
                        {
                            "name": "write_file",
                            "args": {
                                "path": "test_file.txt",
                                "content": "This is a test file created by Trinity"
                            }
                        }
                    ],
                    "execution_report": "File created successfully"
                }''')
            
            else:
                return MagicMock(content='''{
                    "tool_calls": [
                        {
                            "name": "run_shell",
                            "args": {
                                "command": "echo 'Task executed successfully'"
                            }
                        }
                    ],
                    "execution_report": "Task executed via shell command"
                }''')
        
        # Grisha (Verifier) responses
        elif any(keyword in content_lower for keyword in ['verifying', 'grisha', 'verify']):
            if 'calculator' in content_lower:
                return MagicMock(content='''Verification successful. Calculator application is open and responsive. Window title: "Calculator" confirmed. Task completed successfully.''')
            
            elif 'browser' in content_lower:
                return MagicMock(content='''Verification successful. Browser window detected with Google homepage loaded. Search functionality is available. Task completed successfully.''')
            
            elif 'file' in content_lower:
                return MagicMock(content='''Verification successful. File test_file.txt exists with correct content: "This is a test file created by Trinity". Task completed successfully.''')
            
            else:
                return MagicMock(content='''Verification successful. Task execution confirmed through system checks. All expected outcomes achieved. Task completed successfully.''')
        
        # Knowledge (Completion) responses
        elif any(keyword in content_lower for keyword in ['knowledge', 'complete', 'finish']):
            return MagicMock(content='''Task completed successfully. All steps executed and verified. Ready for next task.''')
        
        # Default response
        return MagicMock(content='{"status": "success", "message": "Task processed successfully"}')
    
    mock_llm.invoke = smart_invoke
    return mock_llm

def test_complex_task(task_description, task_type="general"):
    """Test a complex task through the Trinity Runtime"""
    print(f"\n{'='*60}")
    print(f"Testing: {task_description}")
    print(f"Type: {task_type}")
    print(f"{'='*60}")
    
    try:
        with patch('core.trinity.runtime.CopilotLLM') as mock_llm_class:
            mock_llm = create_mock_llm()
            mock_llm_class.return_value = mock_llm
            
            # Create runtime with appropriate permissions
            perms = TrinityPermissions()
            perms.allow_shell = True
            perms.allow_gui = True
            perms.allow_file_write = True
            
            rt = TrinityRuntime(verbose=False, permissions=perms, enable_self_healing=False)
            
            # Run the task with a step limit to prevent infinite loops
            results = []
            max_steps = 15  # Limit steps for testing
            step_count = 0
            
            start_time = datetime.now()
            
            for event in rt.run(task_description, gui_mode='auto', execution_mode='native'):
                results.append(event)
                step_count += 1
                
                # Check for completion
                if event.get('current_agent') == 'end':
                    break
                
                # Safety limit
                if step_count >= max_steps:
                    print(f"⚠️  Reached maximum steps ({max_steps})")
                    break
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Analyze results
            print(f"\n📊 Results:")
            print(f"   Steps executed: {step_count}")
            print(f"   Execution time: {execution_time:.2f} seconds")
            print(f"   Events captured: {len(results)}")
            
            # Check final state
            if results:
                final_event = results[-1]
                final_agent = final_event.get('current_agent', 'unknown')
                messages = final_event.get('messages', [])
                
                print(f"   Final agent: {final_agent}")
                
                if messages:
                    last_message = str(getattr(messages[-1], 'content', ''))
                    print(f"   Final message: {last_message[:100]}...")
                    
                    if 'success' in last_message.lower() or 'completed' in last_message.lower():
                        print(f"   ✅ Task completed successfully")
                        return True
                    elif 'failed' in last_message.lower() or 'error' in last_message.lower():
                        print(f"   ❌ Task failed")
                        return False
                    else:
                        print(f"   ⚠️  Task status unclear")
                        return None
                else:
                    print(f"   ⚠️  No messages in final event")
                    return None
            else:
                print(f"   ❌ No results captured")
                return False
                
    except Exception as e:
        print(f"   ❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive task testing"""
    print("🧪 Trinity Runtime - Complex Task Testing")
    print("=" * 60)
    
    # Test cases covering different scenarios
    test_cases = [
        {
            "description": "Відкрий клькулятор",
            "type": "gui",
            "expected": "success"
        },
        {
            "description": "Знайди в Google інформацію про штучний інтелект",
            "type": "browser",
            "expected": "success"
        },
        {
            "description": "Створи новий файл з текстом 'Hello World'",
            "type": "file",
            "expected": "success"
        },
        {
            "description": "Виконай системну команду для перевірки дискового простору",
            "type": "system",
            "expected": "success"
        },
        {
            "description": "Відкрий браузер і перейди на YouTube",
            "type": "browser",
            "expected": "success"
        }
    ]
    
    results_summary = {
        'total': len(test_cases),
        'success': 0,
        'failed': 0,
        'unclear': 0
    }
    
    # Run all test cases
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}/{len(test_cases)}")
        
        result = test_complex_task(
            test_case['description'],
            test_case['type']
        )
        
        if result is True:
            results_summary['success'] += 1
        elif result is False:
            results_summary['failed'] += 1
        else:
            results_summary['unclear'] += 1
    
    # Print final summary
    print(f"\n{'='*60}")
    print("📊 FINAL TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {results_summary['total']}")
    print(f"✅ Success: {results_summary['success']}")
    print(f"❌ Failed: {results_summary['failed']}")
    print(f"⚠️  Unclear: {results_summary['unclear']}")
    
    success_rate = (results_summary['success'] / results_summary['total']) * 100
    print(f"\n📈 Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 System is working well!")
    elif success_rate >= 50:
        print("⚠️  System needs some improvements")
    else:
        print("❌ System requires significant fixes")
    
    print(f"\n💡 Recommendations will be provided based on test results")

if __name__ == "__main__":
    main()