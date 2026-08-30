"""Lightweight Google Gemini LLM Client for VANTAGE.
Handles intent resolution, persona-specific narrative generation, token accounting,
and cost telemetry with automatic multi-model fallback and rate-limit resiliency.
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CANDIDATE_FLASH_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-flash-latest",
]

CANDIDATE_PRO_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-2.5-pro",
]

@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "gemini-3.5-flash-lite"
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    error: Optional[str] = None

def get_api_key() -> Optional[str]:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None

def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if "pro" in model:
        input_rate = 1.25 / 1_000_000
        output_rate = 5.00 / 1_000_000
    elif "flash-lite" in model:
        input_rate = 0.0375 / 1_000_000
        output_rate = 0.15 / 1_000_000
    else:
        input_rate = 0.075 / 1_000_000
        output_rate = 0.30 / 1_000_000
    return round(input_tokens * input_rate + output_tokens * output_rate, 6)

def call_gemini(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    tier: str = "T1_small_model",
    temperature: float = 0.2,
    json_mode: bool = False,
    timeout_secs: int = 8,
) -> LLMResponse:
    key = get_api_key()
    if not key:
        return LLMResponse(text="", error="GEMINI_API_KEY not configured")

    if model:
        models_to_try = [model]
    elif tier == "T2_frontier":
        models_to_try = CANDIDATE_PRO_MODELS
    else:
        models_to_try = CANDIDATE_FLASH_MODELS

    last_error: Optional[str] = None
    t0 = time.perf_counter()
    ctx = ssl._create_unverified_context()

    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        payload: dict = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1500,
            },
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, context=ctx, timeout=timeout_secs) as response:
                body = json.loads(response.read().decode("utf-8"))

            candidates = body.get("candidates", [])
            if not candidates:
                continue

            parts = candidates[0].get("content", {}).get("parts", [{}])
            text = "".join(p.get("text", "") for p in parts if "text" in p)
            usage = body.get("usageMetadata", {})
            inp = usage.get("promptTokenCount", 0)
            out = usage.get("candidatesTokenCount", 0)
            cost = _calc_cost(m, inp, out)
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            return LLMResponse(
                text=text,
                input_tokens=inp,
                output_tokens=out,
                model=m,
                cost_usd=cost,
                latency_ms=latency_ms,
            )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")[:200]
            last_error = f"HTTP {e.code} on {m}: {err_body}"
            continue
        except Exception as e:
            last_error = f"{type(e).__name__} on {m}: {e}"
            continue

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    return LLMResponse(text="", latency_ms=latency_ms, error=last_error or "All candidate models failed")
