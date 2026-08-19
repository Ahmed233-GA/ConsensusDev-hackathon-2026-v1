import json
import logging
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


def load_dotenv_if_exists():
    """
    Lightweight .env loader that populates/refreshes os.environ from .env file
    in current directory or parent directories.
    """
    search_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for env_path in search_paths:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key:
                            os.environ[key] = val
                break
            except Exception as e:
                logger.warning(f"Error loading .env file from {env_path}: {e}")


# Initial load of .env on import
load_dotenv_if_exists()


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely extract JSON object from LLM response text,
    handling markdown blocks, leading/trailing commentary, etc.
    """
    if not text:
        return None
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try stripping ```json ... ``` blocks
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except Exception:
            pass

    # Try finding outermost { ... }
    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except Exception:
            pass

    return None


class BaseReviewAgent(ABC):
    """
    Base class for all AI Reviewer Agents in ConsensusDev.
    Directly invokes OpenRouter / Cloud LLM models using configured API tokens,
    with automatic JSON parsing and graceful fallback to rule-based heuristics.
    """

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.api_key, self.model_name, self.is_openrouter = self._resolve_config(name)

    def _resolve_config(self, name: str) -> Tuple[Optional[str], str, bool]:
        """
        Resolve API key, Model Name, and Provider (OpenRouter vs direct OpenAI)
        for this specific agent.
        """
        load_dotenv_if_exists()

        # Map agent name to common environment variable prefixes
        key_mappings = {
            "security": ["OPENROUTER_API_KEY_SECURITY", "SECURITY_API_KEY"],
            "tech_debt": ["OPENROUTER_API_KEY_TECH_DEBT", "OPENROUTER_API_KEY_DEBT", "TECH_DEBT_API_KEY", "DEBT_API_KEY"],
            "story_match": ["OPENROUTER_API_KEY_STORY", "OPENROUTER_API_KEY_STORY_MATCH", "STORY_API_KEY"],
            "performance": ["OPENROUTER_API_KEY_PERFORMANCE", "OPENROUTER_API_KEY_PERF", "PERFORMANCE_API_KEY", "PERF_API_KEY"],
        }

        model_mappings = {
            "security": ["SECURITY_AGENT_MODEL", "SECURITY_MODEL"],
            "tech_debt": ["TECH_DEBT_AGENT_MODEL", "DEBT_AGENT_MODEL", "TECH_DEBT_MODEL"],
            "story_match": ["STORY_AGENT_MODEL", "STORY_MATCH_AGENT_MODEL", "STORY_MODEL"],
            "performance": ["PERFORMANCE_AGENT_MODEL", "PERF_AGENT_MODEL", "PERFORMANCE_MODEL"],
        }

        # 1. Resolve API key
        api_key = None
        for env_var in key_mappings.get(name, []):
            val = os.getenv(env_var)
            if val and val.strip() and not val.strip().startswith("sk-or-v1-your-"):
                api_key = val.strip()
                break

        # Fallback to shared OpenRouter or OpenAI keys
        if not api_key:
            for env_var in ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "LITELLM_API_KEY", "GEMINI_API_KEY"]:
                val = os.getenv(env_var)
                if val and val.strip() and not val.strip().startswith("your_") and not val.strip().startswith("sk-or-v1-your-"):
                    api_key = val.strip()
                    break

        # 2. Resolve Model Name
        model_name = None
        for env_var in model_mappings.get(name, []):
            val = os.getenv(env_var)
            if val and val.strip():
                model_name = val.strip()
                break

        if not model_name:
            model_name = (
                os.getenv("OPENROUTER_MODEL")
                or os.getenv("AI_MODEL_NAME")
                or "openai/gpt-4o-mini"
            )

        is_openrouter = bool(
            (api_key and "sk-or-" in api_key)
            or os.getenv("OPENROUTER_API_KEY")
            or any(os.getenv(k) for k in key_mappings.get(name, []) if k.startswith("OPENROUTER_"))
            or "/" in model_name  # e.g. openai/gpt-4o-mini, anthropic/claude-3.5-sonnet
        )

        return api_key, model_name, is_openrouter

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
        Directly invoke the configured OpenRouter / Cloud LLM model with the API key.
        """
        # Re-resolve config dynamically in case .env was updated
        self.api_key, self.model_name, self.is_openrouter = self._resolve_config(self.name)

        if not self.api_key:
            logger.info(f"[{self.name}] No API key configured. Using local heuristic rule engine.")
            return None

        # 1. If OpenRouter is detected, call OpenRouter API via httpx
        if self.is_openrouter:
            try:
                logger.info(f"[{self.name}] Direct Model Execution -> OpenRouter ('{self.model_name}')")
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/Ahmed233-GA/ConsensusDev",
                    "X-Title": f"ConsensusDev AI Engine - {self.name}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                }

                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        parsed = extract_json_from_text(content)
                        if parsed:
                            logger.info(f"[{self.name}] Successfully evaluated with model '{self.model_name}'")
                            return parsed
                        logger.warning(f"[{self.name}] Could not parse JSON from OpenRouter output: {content}")
                    else:
                        logger.warning(
                            f"[{self.name}] OpenRouter API returned HTTP {resp.status_code}: {resp.text}"
                        )
            except Exception as e:
                logger.warning(f"[{self.name}] OpenRouter call exception: {e}")

        # 2. Try OpenAI client as alternative fallback
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
            parsed = extract_json_from_text(raw_content)
            if parsed:
                return parsed
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"[{self.name}] OpenAI call exception: {e}")

        return None
