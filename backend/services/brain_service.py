import json
from typing import Dict, Any
import os
from openai import OpenAI

from ..prompts.system_prompt import get_system_prompt

class BrainService:
    """Service for LLM-powered decision engine to convert voice commands to actions."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

    def decide_action(self, transcript: str, dom_context: str) -> Dict[str, Any]:
        """
        Analyze user transcript and DOM context to generate action plan.

        Args:
            transcript: User's spoken command (transcribed)
            dom_context: JSON string containing page DOM information

        Returns:
            Dictionary with thought, speak_before, and actions
        """
        try:
            user_message = f"""
User Command: {transcript}

DOM Context:
{dom_context}

Based on the user's command and the current page structure, generate the appropriate action plan."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            response_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            action_plan = json.loads(response_text)

            return action_plan

        except json.JSONDecodeError as e:
            return {
                "thought": "Failed to parse LLM response",
                "speak_before": "I encountered an error processing your request. Please try again.",
                "actions": []
            }

        except Exception as e:
            print(f"Brain service error: {str(e)}")
            return {
                "thought": f"Error: {str(e)}",
                "speak_before": "I encountered an error. Please try again.",
                "actions": []
            }