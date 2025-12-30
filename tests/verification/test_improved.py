#!/usr/bin/env python3
"""
Improved Testing Framework for Trinity Runtime
Enhanced testing with better mocking and execution tracing
"""

import os
import sys
import time
from unittest.mock import MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.append(os.getcwd())

from core.trinity import TrinityRuntime, TrinityPermissions
from core.trinity.state import create_initial_state

class TrinityTestFramework:
    """Enhanced testing framework for Trinity Runtime"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        self.current_test = None
        self.start_time = None
        
    def create_smart_mock(self) -> MagicMock:
        """Create an intelligent mock that handles different scenarios"""
        mock_llm = MagicMock()
        
        def smart_invoke(messages):
            """Provide context-aware responses"""
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
                return MagicMock(content='''{
                    "steps": [
                        {
                            "id": 1,
                            "description": "Execute test task",
                            "agent": "tetyana",
                            "tools": ["run_shell"],
                            "expected_result": "Task executed successfully"
                        }
                    ]
                }''')
            
            # Tetyana (Executor) responses
            elif any(keyword in content_lower for keyword in ['executing step', 'tetyana', 'execute']):
                return MagicMock(content='''{
                    "tool_calls": [
                        {
                            "name": "run_shell",
                            "args": {
                                "command": "echo 'Test execution successful'"
                            }
                        }
                    ],
                    "execution_report": "Test task executed successfully"
                }''')
            
            # Grisha (Verifier) responses
            elif any(keyword in content_lower for keyword in ['verifying', 'grisha', 'verify']):
                return MagicMock(content='Verification successful. Test task completed successfully.')
            
            # Default response
            return MagicMock(content='Task completed successfully.')
        
        mock_llm.invoke = smart_invoke
        return mock_llm
    
    def run_test(self, test_name: str, task: str, max_steps: int = 20) -> Dict[str, Any]:
        """Run a single test and return detailed results"""
        self.current_test = test_name
        self.start_time = time.time()
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🧪 Running test: {test_name}")
            print(f"📋 Task: {task}")
            print(f"{'='*60}")
        
        result = {
            'test_name': test_name,
            'task': task,
            'success': False,
            'steps': 0,
            'agents': [],
            'execution_time': 0,
            'error': None,
            'trace': []
        }
        
        try:
            with patch('core.trinity.runtime.CopilotLLM') as mock_llm_class:
                mock_llm = self.create_smart_mock()
                mock_llm_class.return_value = mock_llm
                
                # Create runtime with appropriate permissions
                perms = TrinityPermissions()
                perms.allow_shell = True
                perms.allow_gui = True
                perms.allow_file_write = True
                
                rt = TrinityRuntime(verbose=self.verbose, permissions=perms, enable_self_healing=False)
                
                # Run the task with execution tracing
                results = []
                step_count = 0
                
                for event in rt.run(task, gui_mode='off', execution_mode='native'):
                    results.append(event)
                    step_count += 1
                    
                    # Log execution step
                    agent = event.get('current_agent', 'unknown')
                    result['agents'].append(agent)
                    
                    # Check for completion
                    if agent == 'end':
                        break
                    
                    # Safety limit
                    if step_count >= max_steps:
                        if self.verbose:
                            print(f"⚠️  Reached maximum steps: {max_steps}")
                        break
                
                # Record results
                result['steps'] = step_count
                result['execution_time'] = time.time() - self.start_time
                result['trace'] = rt.get_execution_trace()
                result['stats'] = rt.get_execution_stats()
                
                # Check final state
                if results:
                    final_event = results[-1]
                    final_agent = final_event.get('current_agent', 'unknown')
                    messages = final_event.get('messages', [])
                    
                    if messages:
                        last_message = str(getattr(messages[-1], 'content', ''))
                        if 'success' in last_message.lower() or 'completed' in last_message.lower():
                            result['success'] = True
                            if self.verbose:
                                print(f"✅ Test completed successfully")
                        else:
                            result['success'] = False
                            if self.verbose:
                                print(f"❌ Test failed or unclear")
                    else:
                        result['success'] = False
                        if self.verbose:
                            print(f"⚠️  No messages in final event")
                else:
                    result['success'] = False
                    if self.verbose:
                        print(f"❌ No results captured")
                
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            if self.verbose:
                print(f"❌ Exception occurred: {e}")
                import traceback
                traceback.print_exc()
        
        # Store result
        self.test_results.append(result)
        return result
    
    def run_test_suite(self, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """Run a suite of tests and return summary"""
        summary = {
            'total': len(test_cases),
            'success': 0,
            'failed': 0,
            'unclear': 0,
            'results': []
        }
        
        for test_case in test_cases:
            result = self.run_test(
                test_case['name'],
                test_case['task'],
                test_case.get('max_steps', 20)
            )
            
            summary['results'].append(result)
            
            if result['success']:
                summary['success'] += 1
            elif result['error']:
                summary['failed'] += 1
            else:
                summary['unclear'] += 1
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary in a readable format"""
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {summary['total']}")
        print(f"✅ Success: {summary['success']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Unclear: {summary['unclear']}")
        
        if summary['total'] > 0:
            success_rate = (summary['success'] / summary['total']) * 100
            print(f"\n📈 Success rate: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print("🎉 Excellent performance!")
            elif success_rate >= 50:
                print("⚠️  Good performance, room for improvement")
            else:
                print("❌ Needs significant improvement")
        
        # Print detailed results for failed tests
        if summary['failed'] > 0:
            print(f"\n🔍 Failed tests:")
            for result in summary['results']:
                if not result['success'] and result['error']:
                    print(f"   - {result['test_name']}: {result['error']}")

def main():
    """Run comprehensive testing"""
    print("🚀 Trinity Runtime - Improved Testing Framework")
    print("=" * 60)
    
    # Create test framework
    tester = TrinityTestFramework(verbose=True)
    
    # Define test cases
    test_cases = [
        {
            'name': 'Simple Task Execution',
            'task': 'Execute a simple test task',
            'max_steps': 15
        },
        {
            'name': 'Calculator Test',
            'task': 'Open calculator application',
            'max_steps': 15
        },
        {
            'name': 'File Creation Test',
            'task': 'Create a test file with sample content',
            'max_steps': 15
        },
        {
            'name': 'System Command Test',
            'task': 'Run a system command to check disk space',
            'max_steps': 15
        },
        {
            'name': 'Browser Test',
            'task': 'Open browser and navigate to homepage',
            'max_steps': 15
        }
    ]
    
    # Run test suite
    print(f"\n📋 Running {len(test_cases)} tests...")
    summary = tester.run_test_suite(test_cases)
    
    # Print summary
    tester.print_summary(summary)
    
    # Print execution statistics for successful tests
    if summary['success'] > 0:
        print(f"\n📊 Execution Statistics:")
        total_steps = 0
        total_time = 0
        
        for result in summary['results']:
            if result['success']:
                total_steps += result['steps']
                total_time += result['execution_time']
        
        if summary['success'] > 0:
            avg_steps = total_steps / summary['success']
            avg_time = total_time / summary['success']
            print(f"   Average steps: {avg_steps:.1f}")
            print(f"   Average time: {avg_time:.2f} seconds")
    
    print(f"\n✅ Testing completed!")

if __name__ == "__main__":
    main()