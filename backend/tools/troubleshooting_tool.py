# backend/tools/troubleshooting_tool.py

"""
Troubleshooting tool module.

Provides structured troubleshooting steps for common device issues,
based on a JSON knowledge base in data/structured/troubleshooting.json.

This tool is useful for queries like:
- "My laptop is not turning on."
- "My headphones have no sound."
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from langchain_core.tools import tool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRUCTURED_DATA_DIR = PROJECT_ROOT / "data" / "structured"
TROUBLESHOOTING_PATH = STRUCTURED_DATA_DIR / "troubleshooting.json"


def load_troubleshooting_kb() -> Dict[str, Any]:
    if not TROUBLESHOOTING_PATH.exists():
        raise FileNotFoundError(f"troubleshooting.json not found at: {TROUBLESHOOTING_PATH}")
    with open(TROUBLESHOOTING_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("troubleshooting.json must contain a JSON object at the top level.")
    return data


# def normalize_product_type(product_type: str) -> str:
    pt = product_type.lower().strip()
    if "laptop" in pt:
        return "laptop"
    if "headphone" in pt:
        return "headphones"
    if "phone" in pt or "mobile" in pt:
        return "phone"
    return pt
def normalize_product_type(product_type: str) -> str:
    pt = product_type.lower().strip()
    if "laptop" in pt:
        return "laptop"
    if "headphone" in pt:
        return "headphones"
    if "phone" in pt or "mobile" in pt:
        return "phone"
    if "device" in pt:
        # For generic "device", treat as a laptop-like device in this demo
        return "laptop"
    return pt


def normalize_issue(issue: str) -> str:
    text = issue.lower()
    if "not turning on" in text or "won't turn on" in text or "does not turn on" in text or "won't power on" in text:
        return "not_turning_on"
    if "no sound" in text or "cannot hear" in text or "no audio" in text:
        return "no_sound"
    if "overheating" in text or "too hot" in text:
        return "overheating"
    # default: return as-is, might not match the KB
    return issue.replace(" ", "_").lower()


@tool("get_troubleshooting_steps", return_direct=False)
def get_troubleshooting_steps_tool(product_type: str, issue: str) -> Dict[str, Any]:
    """
    Retrieve structured troubleshooting steps for a given product type and issue.

    Args:
        product_type: e.g. "laptop", "headphones"
        issue: natural language description, e.g. "not turning on", "no sound"

    Returns:
        {
          "found": bool,
          "product_type": str,
          "issue_key": str,
          "steps": List[str],
          "message": str,
        }
    """
    kb = load_troubleshooting_kb()

    norm_product = normalize_product_type(product_type)
    norm_issue = normalize_issue(issue)

    product_entry = kb.get(norm_product)
    if product_entry is None:
        return {
            "found": False,
            "product_type": norm_product,
            "issue_key": norm_issue,
            "steps": [],
            "message": f"No troubleshooting data found for product type '{norm_product}'.",
        }

    steps: List[str] = product_entry.get(norm_issue, [])

    if not steps:
        return {
            "found": False,
            "product_type": norm_product,
            "issue_key": norm_issue,
            "steps": [],
            "message": f"No troubleshooting steps found for issue '{norm_issue}' on '{norm_product}'.",
        }

    # Build a human-readable message summarizing the steps
    lines = [f"Here are some troubleshooting steps for your {norm_product} ({issue}):"]
    for i, step in enumerate(steps, start=1):
        lines.append(f"{i}. {step}")
    message = "\n".join(lines)

    return {
        "found": True,
            "product_type": norm_product,
            "issue_key": norm_issue,
            "steps": steps,
            "message": message,
    }
