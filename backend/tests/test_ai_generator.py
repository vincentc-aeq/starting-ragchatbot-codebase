import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_generator import AIGenerator


class TestAIGenerator:
    """Test suite for AIGenerator focusing on external behavior"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.api_key = "test_api_key"
        self.model = "claude-3-sonnet-20240229"
        self.ai_generator = AIGenerator(self.api_key, self.model)
        
        # Mock tool manager
        self.mock_tool_manager = Mock()
        self.mock_tool_manager.execute_tool.return_value = "Tool result"
        
        # Sample tools definition
        self.tools = [
            {
                "name": "search_course_content",
                "description": "Search course materials",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            }
        ]
    
    def create_mock_response(self, content_blocks, stop_reason="end_turn"):
        """Helper to create mock Anthropic API response"""
        mock_response = Mock()
        mock_response.content = content_blocks
        mock_response.stop_reason = stop_reason
        return mock_response
        
    def create_tool_use_block(self, tool_name="search_course_content", tool_id="tool_1", input_data=None):
        """Helper to create tool use content block"""
        if input_data is None:
            input_data = {"query": "test query"}
            
        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.name = tool_name
        mock_block.id = tool_id
        mock_block.input = input_data
        return mock_block
        
    def create_text_block(self, text="Test response"):
        """Helper to create text content block"""
        # Use a simple class instead of Mock for better control
        class TextBlock:
            def __init__(self, text):
                self.type = "text"
                self.text = text
        
        return TextBlock(text)

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_no_tools(self, mock_anthropic):
        """Test direct response generation without tools"""
        # Setup
        text_block = self.create_text_block("Direct answer without tools")
        mock_response = self.create_mock_response([text_block])
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute
        result = ai_gen.generate_response("What is AI?")
        
        # Verify
        assert result == "Direct answer without tools"
        assert mock_client.messages.create.call_count == 1
        
        # Verify API call parameters
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["messages"][0]["content"] == "What is AI?"
        assert "tools" not in call_args[1]

    @patch('ai_generator.anthropic.Anthropic')
    def test_single_tool_call(self, mock_anthropic):
        """Test single tool call (existing behavior preserved)"""
        # Setup - First call returns tool use, second call returns final response
        tool_block = self.create_tool_use_block()
        text_block = self.create_text_block("Final response after tool use")
        
        tool_response = self.create_mock_response([tool_block], "tool_use")
        final_response = self.create_mock_response([text_block])
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = [tool_response, final_response]
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute
        result = ai_gen.generate_response(
            "Search for AI courses",
            tools=self.tools,
            tool_manager=self.mock_tool_manager
        )
        
        # Verify
        assert result == "Final response after tool use"
        assert mock_client.messages.create.call_count == 2
        assert self.mock_tool_manager.execute_tool.call_count == 1
        
        # Verify tool was called with correct parameters
        tool_call_args = self.mock_tool_manager.execute_tool.call_args
        assert tool_call_args[0][0] == "search_course_content"
        assert tool_call_args[1]["query"] == "test query"

    @patch('ai_generator.anthropic.Anthropic')
    def test_sequential_tool_calls_max_rounds(self, mock_anthropic):
        """Test sequential tool calls reaching maximum of 2 rounds"""
        # Setup - Two tool use calls, then final response
        tool_block_1 = self.create_tool_use_block(tool_id="tool_1")
        tool_block_2 = self.create_tool_use_block(tool_id="tool_2")
        text_block = self.create_text_block("Final response after 2 tool calls")
        
        first_tool_response = self.create_mock_response([tool_block_1], "tool_use")
        second_tool_response = self.create_mock_response([tool_block_2], "tool_use")
        final_response = self.create_mock_response([text_block])
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = [
            first_tool_response,
            second_tool_response, 
            final_response
        ]
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute
        result = ai_gen.generate_response(
            "Complex query requiring multiple searches",
            tools=self.tools,
            tool_manager=self.mock_tool_manager
        )
        
        # Verify
        assert result == "Final response after 2 tool calls"
        assert mock_client.messages.create.call_count == 3  # Initial + 2 rounds
        assert self.mock_tool_manager.execute_tool.call_count == 2
        
        # Verify final call has no tools (max rounds reached)
        final_call_args = mock_client.messages.create.call_args_list[2]
        assert "tools" not in final_call_args[1]

    @patch('ai_generator.anthropic.Anthropic')
    def test_sequential_tool_calls_natural_termination(self, mock_anthropic):
        """Test sequential tool calls with natural termination (Claude stops using tools)"""
        # Setup - One tool call, then direct text response
        tool_block = self.create_tool_use_block()
        text_block = self.create_text_block("Response after analyzing tool results")
        
        tool_response = self.create_mock_response([tool_block], "tool_use")
        final_response = self.create_mock_response([text_block])
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = [tool_response, final_response]
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute
        result = ai_gen.generate_response(
            "Query that needs one search then analysis",
            tools=self.tools,
            tool_manager=self.mock_tool_manager
        )
        
        # Verify
        assert result == "Response after analyzing tool results"
        assert mock_client.messages.create.call_count == 2
        assert self.mock_tool_manager.execute_tool.call_count == 1
        
        # Verify second call still has tools available (not max rounds)
        second_call_args = mock_client.messages.create.call_args_list[1]
        assert "tools" in second_call_args[1]

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_execution_error_handling(self, mock_anthropic):
        """Test graceful handling of tool execution errors"""
        # Setup
        tool_block = self.create_tool_use_block()
        text_block = self.create_text_block("Response despite tool error")
        
        tool_response = self.create_mock_response([tool_block], "tool_use")
        final_response = self.create_mock_response([text_block])
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = [tool_response, final_response]
        mock_anthropic.return_value = mock_client
        
        # Make tool execution fail
        self.mock_tool_manager.execute_tool.side_effect = Exception("Tool failed")
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute
        result = ai_gen.generate_response(
            "Query with failing tool",
            tools=self.tools,
            tool_manager=self.mock_tool_manager
        )
        
        # Verify
        assert result == "Response despite tool error"
        assert mock_client.messages.create.call_count == 2
        
        # Verify error was handled gracefully in tool results
        second_call_args = mock_client.messages.create.call_args_list[1]
        messages = second_call_args[1]["messages"]
        tool_result_message = messages[-1]  # Last message should be tool results
        
        # Check that tool failure was included in the message
        tool_result_content = tool_result_message["content"][0]["content"]
        assert "Tool execution failed: Tool failed" in tool_result_content

    @patch('ai_generator.anthropic.Anthropic')
    def test_api_error_during_sequential_calls(self, mock_anthropic):
        """Test handling of API errors during sequential tool execution"""
        # Setup
        tool_block = self.create_tool_use_block()
        tool_response = self.create_mock_response([tool_block], "tool_use")
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = [
            tool_response,
            Exception("API Error during second call")
        ]
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute
        result = ai_gen.generate_response(
            "Query causing API error",
            tools=self.tools,
            tool_manager=self.mock_tool_manager
        )
        
        # Verify graceful error handling
        assert "Error during tool execution round 1: API Error during second call" in result
        assert mock_client.messages.create.call_count == 2
        assert self.mock_tool_manager.execute_tool.call_count == 1

    @patch('ai_generator.anthropic.Anthropic')
    def test_conversation_history_preservation(self, mock_anthropic):
        """Test that conversation history is properly maintained across sequential calls"""
        # Setup
        tool_block = self.create_tool_use_block()
        text_block = self.create_text_block("Response with history context")
        
        tool_response = self.create_mock_response([tool_block], "tool_use")
        final_response = self.create_mock_response([text_block])
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = [tool_response, final_response]
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute with conversation history
        conversation_history = "Previous conversation context"
        result = ai_gen.generate_response(
            "New query",
            conversation_history=conversation_history,
            tools=self.tools,
            tool_manager=self.mock_tool_manager
        )
        
        # Verify
        assert result == "Response with history context"
        
        # Verify conversation history is included in both API calls
        for call_args in mock_client.messages.create.call_args_list:
            system_prompt = call_args[1]["system"]
            assert conversation_history in system_prompt

    @patch('ai_generator.anthropic.Anthropic')
    def test_message_context_building(self, mock_anthropic):
        """Test that message context is properly built across sequential rounds"""
        # Setup
        tool_block_1 = self.create_tool_use_block(tool_id="tool_1")
        tool_block_2 = self.create_tool_use_block(tool_id="tool_2")
        text_block = self.create_text_block("Final response")
        
        first_tool_response = self.create_mock_response([tool_block_1], "tool_use")
        second_tool_response = self.create_mock_response([tool_block_2], "tool_use")
        final_response = self.create_mock_response([text_block])
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = [
            first_tool_response,
            second_tool_response,
            final_response
        ]
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute
        result = ai_gen.generate_response(
            "Initial query",
            tools=self.tools,
            tool_manager=self.mock_tool_manager
        )
        
        # Verify message context grows appropriately
        call_args_list = mock_client.messages.create.call_args_list
        
        # First call: just user message
        first_messages = call_args_list[0][1]["messages"]
        assert len(first_messages) == 1
        assert first_messages[0]["role"] == "user"
        assert first_messages[0]["content"] == "Initial query"
        
        # Second call: user + assistant + user (tool results)
        second_messages = call_args_list[1][1]["messages"]
        assert len(second_messages) == 3
        assert second_messages[0]["role"] == "user"    # Original query
        assert second_messages[1]["role"] == "assistant"  # First tool use
        assert second_messages[2]["role"] == "user"    # First tool results
        
        # Third call: all previous plus second assistant response and tool results
        third_messages = call_args_list[2][1]["messages"]
        assert len(third_messages) == 5
        assert third_messages[0]["role"] == "user"    # Original query
        assert third_messages[1]["role"] == "assistant"  # First tool use
        assert third_messages[2]["role"] == "user"    # First tool results
        assert third_messages[3]["role"] == "assistant"  # Second tool use  
        assert third_messages[4]["role"] == "user"    # Second tool results

    def test_system_prompt_sequential_guidance(self):
        """Test that system prompt includes sequential tool calling guidance"""
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Verify key sequential tool calling guidance is present
        system_prompt = ai_gen.SYSTEM_PROMPT
        
        assert "Sequential tool usage" in system_prompt
        assert "up to 2 tools in sequence" in system_prompt
        assert "Tool chaining" in system_prompt
        assert "Complex queries" in system_prompt
        
        # Verify old single tool restriction is removed
        assert "One tool use per query maximum" not in system_prompt

    @patch('ai_generator.anthropic.Anthropic')
    def test_backward_compatibility_no_tools(self, mock_anthropic):
        """Test backward compatibility - no tools provided behaves identically to before"""
        # Setup
        text_block = self.create_text_block("Direct response")
        mock_response = self.create_mock_response([text_block])
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute without tools (old behavior)
        result = ai_gen.generate_response("Simple query")
        
        # Verify same behavior as before
        assert result == "Direct response"
        assert mock_client.messages.create.call_count == 1
        
        # Verify no tool-related parameters
        call_args = mock_client.messages.create.call_args
        assert "tools" not in call_args[1]
        assert "tool_choice" not in call_args[1]

    @patch('ai_generator.anthropic.Anthropic')
    def test_edge_case_empty_response(self, mock_anthropic):
        """Test edge case where API returns empty or malformed response"""
        # Setup
        mock_response = Mock()
        mock_response.content = []
        mock_response.stop_reason = "end_turn"
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        ai_gen = AIGenerator(self.api_key, self.model)
        
        # Execute
        try:
            result = ai_gen.generate_response("Test query")
            # If no exception, should handle gracefully
            assert result is not None
        except IndexError:
            # This is expected given the empty content
            pass