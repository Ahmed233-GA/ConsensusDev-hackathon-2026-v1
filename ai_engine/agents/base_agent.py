import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class BaseReviewAgent(ABC):
    """
    Base class for all AI Reviewer Agents in ConsensusDev.
    Provides standard diff parsing, LLM call abstraction, and rule-based heuristic fallback.
    """

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.model_name = os.getenv("AI_MODEL_NAME", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LITELLM_API_KEY")

    @abstractmethod
    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        """
        Evaluate the PR diff within the given context (scanner reports, QA test results, user story).
        Returns an AgentEvaluation object.
        """
        pass

    def extract_diff_metadata(self, diff: str) -> Dict[str, Any]:
        """
        Extract added lines, removed lines, and filenames from git diff.
        """
        added_lines: List[Tuple[str, str]] = []  # (filename, line_content)
        removed_lines: List[Tuple[str, str]] = []
        files_changed: List[str] = []
        current_file = "unknown"

        for line in diff.splitlines():
            if line.startswith("diff --git"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    current_file = parts[3].lstrip("b/")
                    if current_file not in files_changed:
                        files_changed.append(current_file)
            elif line.startswith("+++ b/"):
                current_file = line.replace("+++ b/", "").strip()
                if current_file not in files_changed:
                    files_changed.append(current_file)
            elif line.startswith("+") and not line.startswith("+++"):
                added_lines.append((current_file, line[1:]))
            elif line.startswith("-") and not line.startswith("---"):
                removed_lines.append((current_file, line[1:]))

        return {
            "files_changed": files_changed,
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "total_additions": len(added_lines),
            "total_deletions": len(removed_lines),
        }

    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to call LLM using litellm or openai.
        If not configured or if an error occurs, returns None to allow heuristic fallback.
        """
        if not self.api_key:
            return None

        # Try LiteLLM first
        try:
            import litellm

            response = await litellm.acompletion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"LiteLLM call failed for {self.name}: {e}. Falling back...")

        # Try OpenAI client as fallback
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"OpenAI call failed for {self.name}: {e}. Falling back...")

        return None
