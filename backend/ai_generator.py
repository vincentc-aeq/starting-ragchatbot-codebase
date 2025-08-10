from typing import Any, Dict, List, Optional

import anthropic


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Tool Usage Guidelines:
- **Course outline/structure questions**: Use get_course_outline tool to provide course title, course link, and complete lesson list with lesson numbers and titles
- **Content-specific questions**: Use search_course_content tool for detailed educational materials and lesson content
- **Sequential tool usage**: You may use up to 2 tools in sequence if needed to fully answer the question
- **Tool chaining**: After seeing results from one tool, you may use another tool if the first results indicate additional information is needed
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course outline questions**: Use outline tool, then provide complete course structure including title, link, and all lessons
- **Course content questions**: Use search tool, then answer based on results
- **Complex queries**: Use multiple tools if first tool results suggest additional searches would be helpful
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the search results" or "using the tool"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content,
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Handle sequential tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_sequential_tool_execution(
                response, api_params, tool_manager
            )

        # Return direct response
        return response.content[0].text

    def _handle_sequential_tool_execution(
        self, initial_response, base_params: Dict[str, Any], tool_manager
    ):
        """
        Handle sequential execution of up to 2 tool calls across separate API rounds.

        Args:
            initial_response: The response containing first tool use request
            base_params: Base API parameters
            tool_manager: Manager to execute tools

        Returns:
            Final response text after all tool executions
        """
        messages = base_params["messages"].copy()
        current_response = initial_response
        max_rounds = 2
        round_count = 0

        while round_count < max_rounds and current_response.stop_reason == "tool_use":

            round_count += 1

            # Add AI's tool use response to conversation
            messages.append({"role": "assistant", "content": current_response.content})

            # Execute tools from current response
            tool_results = []

            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        tool_result = tool_manager.execute_tool(
                            content_block.name, **content_block.input
                        )

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": tool_result,
                            }
                        )
                    except Exception as e:
                        # Handle tool execution errors gracefully
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": f"Tool execution failed: {str(e)}",
                            }
                        )

            # Add tool results to conversation
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Note: Continue even if tool execution failed - Claude can still provide response
            # based on the error information in the tool results

            # Prepare API call for next round (keep tools available)
            next_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"],
            }

            # Include tools only if we haven't reached max rounds
            if round_count < max_rounds:
                next_params["tools"] = base_params.get("tools", [])
                next_params["tool_choice"] = {"type": "auto"}

            # Make API call for next round
            try:
                current_response = self.client.messages.create(**next_params)
            except Exception as e:
                # Handle API errors gracefully
                return f"Error during tool execution round {round_count}: {str(e)}"

        # Return final response content
        if hasattr(current_response, "content") and current_response.content:
            return current_response.content[0].text
        else:
            return "Unable to generate response after tool execution."
