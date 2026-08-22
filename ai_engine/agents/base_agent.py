import asyncio
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


def load_dotenv():
    """
    Load environment variables from .env file into os.environ.
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
                logger.warning(f"Error loading .env from {env_path}: {e}")


# Load on import
load_dotenv()


def extract_json_from_llm(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON dictionary from raw LLM output text.
    Handles raw JSON, markdown code blocks (```json ... ```), and surrounded text.
    """
    if not text:
        return None
    text = text.strip()

    # 1. Direct JSON parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Markdown fenced code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # 3. Outermost curly braces
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return None


class BaseReviewAgent(ABC):
    """
    Base class for all ConsensusDev AI Reviewer Agents.
    Directly communicates with OpenRouter / Cloud LLM APIs using configured tokens.
    """

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.api_key, self.model_name, self.is_openrouter = self._resolve_config(name)

    def _resolve_config(self, name: str) -> Tuple[Optional[str], str, bool]:
        load_dotenv()

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

        if not api_key:
            for env_var in ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "LITELLM_API_KEY", "GEMINI_API_KEY"]:
                val = os.getenv(env_var)
                if val and val.strip() and not val.strip().startswith("your_") and not val.strip().startswith("sk-or-v1-your-"):
                    api_key = val.strip()
                    break

        # 2. Resolve Model
        model_name = None
        for env_var in model_mappings.get(name, []):
            val = os.getenv(env_var)
            if val and val.strip():
                model_name = val.strip()
                break

        if not model_name:
            model_name = os.getenv("OPENROUTER_MODEL") or os.getenv("AI_MODEL_NAME") or "openai/gpt-4o-mini"

        is_openrouter = bool(
            (api_key and "sk-or-" in api_key)
            or os.getenv("OPENROUTER_API_KEY")
            or any(os.getenv(k) for k in key_mappings.get(name, []) if k.startswith("OPENROUTER_"))
            or "/" in model_name
        )

        return api_key, model_name, is_openrouter

    @abstractmethod
    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        """Evaluate PR diff using the LLM model."""
        pass

    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """
        Send prompt directly to OpenRouter / Cloud LLM API and parse JSON output.
        """
        # Refresh configuration in case .env changed
        self.api_key, self.model_name, self.is_openrouter = self._resolve_config(self.name)

        if not self.api_key:
            logger.warning(
                f"[{self.name}] No LLM API key found in .env (set OPENROUTER_API_KEY or OPENROUTER_API_KEY_{self.name.upper()})."
            )
            return None

        # 1. Direct OpenRouter API Call
        if self.is_openrouter:
            candidate_models = [self.model_name]
            # Fallback model if primary is rate limited or unavailable
            fallback_model = "cohere/north-mini-code:free" if self.model_name != "cohere/north-mini-code:free" else "nvidia/nemotron-3-super-120b-a12b:free"
            if fallback_model not in candidate_models:
                candidate_models.append(fallback_model)

            for model_to_try in candidate_models:
                try:
                    logger.info(f"[{self.name}] Calling OpenRouter Model: '{model_to_try}'...")
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://github.com/Ahmed233-GA/ConsensusDev",
                        "X-Title": f"ConsensusDev AI Reviewer - {self.name}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": model_to_try,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": temperature,
                    }

                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=payload,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data["choices"][0]["message"].get("content")
                            if content:
                                parsed = extract_json_from_llm(content)
                                if parsed:
                                    logger.info(f"[{self.name}] LLM evaluation received from '{model_to_try}'")
                                    return parsed
                            logger.warning(f"[{self.name}] Could not extract JSON from '{model_to_try}': {content}")
                        elif resp.status_code == 429:
                            logger.warning(f"[{self.name}] Model '{model_to_try}' rate limited (429). Trying fallback...")
                            await asyncio.sleep(2.0)
                        else:
                            logger.warning(f"[{self.name}] OpenRouter HTTP {resp.status_code} for '{model_to_try}': {resp.text}")
                except Exception as e:
                    logger.error(f"[{self.name}] OpenRouter attempt for '{model_to_try}' failed: {e}")

        return None
