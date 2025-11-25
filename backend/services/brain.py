import json
from typing import Dict, Any
from openai import OpenAI
from config import config

class Brain:
    """LLM-powered decision engine using Grok (xAI)."""

    def __init__(self):
        self.client = OpenAI(
            api_key=config.XAI_API_KEY,
            base_url=config.XAI_BASE_URL
        )
        self.model = config.XAI_MODEL

    def decide_action(self, transcript: str, dom_json: str) -> Dict[str, Any]:
        """
        Analyze transcript and DOM context to generate action plan.

        Args:
            transcript: User's spoken command
            dom_json: JSON string of page DOM

        Returns:
            Dictionary with thought_process, voice_response_text, and actions
        """
        try:
            user_message = f"""User Command: {transcript}

DOM Context:
{dom_json}

Analyze the command and DOM context. Respond ONLY with the JSON object matching the schema provided in the system prompt."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
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

            response_text = self._strip_markdown(response_text)

            action_plan = json.loads(response_text)
            return action_plan

        except json.JSONDecodeError as e:
            return {
                "thought_process": "Failed to parse LLM response",
                "voice_response_text": "I encountered an error processing your request. Please try again.",
                "actions": []
            }

        except Exception as e:
            print(f"Brain error: {str(e)}")
            return {
                "thought_process": f"Error: {str(e)}",
                "voice_response_text": "I encountered an error. Please try again.",
                "actions": []
            }

    def _strip_markdown(self, text: str) -> str:
        """Remove markdown code blocks from response."""
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _get_system_prompt(self) -> str:
        """Return the system prompt for action generation."""
        return """You are Voice Samurai. You control a web browser.

Input: User Transcript + List of Interactable Elements (ID, Tag, Text).
Output: JSON Object.

You MUST respond with ONLY valid JSON, no other text. No markdown, no explanation, no code blocks.

REQUIRED SCHEMA:
{
  "thought_process": "Brief reasoning about what the user wants",
  "voice_response_text": "What you will say to the user (e.g. 'Opening settings')",
  "actions": [
    {
      "action_type": "click" | "fill" | "scroll" | "navigate",
      "target_id": "The data-v-id from context (required for click/fill)",
      "value": "Text to type (required for fill)",
      "scroll_amount": 500,
      "url": "https://example.com (required for navigate)"
    }
  ]
}

ACTION TYPES:
- "click": Click on an element. REQUIRES: target_id
- "fill": Type text into input. REQUIRES: target_id, value
- "scroll": Scroll page. REQUIRES: scroll_amount (pixels)
- "navigate": Navigate to URL. REQUIRES: url

CRITICAL RULES:
1. ALWAYS return ONLY valid JSON - no markdown, no code blocks
2. Use target_id from provided DOM context (data-v-id attribute)
3. For empty actions, return: "actions": []
4. For fill actions, include both target_id AND value
5. For scroll, use positive numbers (e.g., 500)
6. For navigate, include full URL with https://
7. Never use CSS selectors - ONLY use data-v-id
8. If unclear, ask clarification in voice_response_text

Now analyze the user's command and DOM context. Respond with ONLY the JSON object."""
