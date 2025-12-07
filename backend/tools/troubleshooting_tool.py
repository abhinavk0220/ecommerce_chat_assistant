# tools/troubleshooting_tool.py

"""
Simple troubleshooting tool for common issues.

We support basic, rule-based troubleshooting for:
- laptops
- headphones

The idea:
- Map the user's free-text "issue" into a normalized issue key.
- Look up predefined troubleshooting steps.
- Return a structured JSON object that the orchestrator can convert into
  a natural language answer.
"""

from __future__ import annotations

from typing import Dict, Any, List

# Predefined troubleshooting steps
TROUBLESHOOTING_DATA: Dict[str, Dict[str, List[str]]] = {
    "laptop": {
        "not_turning_on": [
            "Check the power cable and ensure it is firmly connected.",
            "Verify that the wall outlet is working by testing another device.",
            "If the battery is removable, remove it, connect the power cable, and hold the power button for 10 seconds.",
            "If the laptop still does not turn on, contact support.",
        ],
        "overheating": [
            "Ensure that the laptop vents are not blocked and are free of dust.",
            "Use the laptop on a hard, flat surface for better airflow.",
            "Close heavy background applications that might be stressing the CPU or GPU.",
            "If overheating continues, consider cleaning the fan or contacting support.",
        ],
        "not_working_generic": [
            "Restart the laptop and check if the issue persists.",
            "Make sure your operating system and drivers are up to date.",
            "Check if the issue is limited to a specific app or happens everywhere.",
            "If the problem continues, note down any error messages and contact support.",
        ],
    },
    "headphones": {
        "no_sound": [
            "Check the Bluetooth connection or audio cable connection.",
            "Ensure the volume is not muted on the connected device.",
            "Try pairing the headphones with another device to isolate the issue.",
        ],
        "distorted_sound": [
            "Reduce the volume slightly to see if the sound becomes clearer.",
            "Check if the audio source quality is low or heavily compressed.",
            "Try a different app or media file to confirm.",
        ],
        "not_working_generic": [
            "Check if the headphones are powered on and sufficiently charged.",
            "Unpair and re-pair the headphones with your device.",
            "Test the headphones with a different phone or laptop to see if the issue is device-specific.",
            "If the problem persists, you may need to contact support or explore warranty options.",
        ],
    },
}


def _normalize_product_type(product_type: str) -> str:
    lowered = (product_type or "").lower()
    if "laptop" in lowered:
        return "laptop"
    if "headphone" in lowered or "headset" in lowered:
        return "headphones"
    # default fallback type
    return "laptop"


def _infer_issue_key(product_type: str, issue: str) -> str | None:
    lowered = issue.lower()

    # --- MATCHING LOGIC ---

    # 1. Power / Not Turning On
    if (
        "not turning on" in lowered
        or "won't turn on" in lowered
        or "does not turn on" in lowered
        or "doesn't turn on" in lowered
        or "won't power on" in lowered
        or "dead" in lowered
        or "no power" in lowered
    ):
        return "not_turning_on"

    # 2. Sound / Audio Issues
    if (
        "no sound" in lowered 
        or "no audio" in lowered 
        or "cannot hear" in lowered
        or "silent" in lowered
    ):
        return "no_sound"

    # 3. Overheating / Heat (EXPANDED THIS SECTION)
    if (
        "overheat" in lowered 
        or "too hot" in lowered 
        or "getting hot" in lowered
        or "heating" in lowered   # Added "heating"
        or "heat" in lowered      # Added "heat"
        or "hot" in lowered       # Added generic "hot"
    ):
        return "overheating"

    # 4. Generic "not working" phrases
    if (
        "not working" in lowered 
        or "not working properly" in lowered 
        or "stopped working" in lowered
        or "broken" in lowered
    ):
        return "not_working_generic"

    # If nothing matched, return None
    return None


class GetTroubleshootingStepsTool:
    """
    Simple tool class for getting troubleshooting steps.
    """
    def __init__(self):
        self.name = "get_troubleshooting_steps"
        self.description = "Get troubleshooting steps for common device issues"
    
    def invoke(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool: get_troubleshooting_steps
        
        Args:
            input_dict: Dict with 'product_type' and 'issue' keys
        
        Returns:
            dict with keys:
            - found: bool
            - product_type: normalized product type
            - issue_key: normalized issue key (if found)
            - steps: list of steps (if found)
            - message: human-readable summary
        """
        product_type = input_dict.get("product_type", "laptop")
        issue = input_dict.get("issue", "")
        
        norm_type = _normalize_product_type(product_type)
        issue_key = _infer_issue_key(norm_type, issue)
        
        data_for_type = TROUBLESHOOTING_DATA.get(norm_type, {})
        steps = data_for_type.get(issue_key) if issue_key else None
        
        if steps:
            # Build a friendly message
            pretty_issue = issue_key.replace("_", " ")
            lines = [
                f"Here are some troubleshooting steps for your {norm_type} ({pretty_issue}):"
            ]
            for i, step in enumerate(steps, start=1):
                lines.append(f"{i}. {step}")
            message = "\n".join(lines)
            
            return {
                "found": True,
                "product_type": norm_type,
                "issue_key": issue_key,
                "steps": steps,
                "message": message,
            }
        
        # If we didn't find a match, return a structured "not found" response
        return {
            "found": False,
            "product_type": norm_type,
            "issue_key": None,
            "steps": [],
            "message": (
                f"No troubleshooting steps found for issue '{issue}' on '{norm_type}'. "
                "You can try describing the problem in more detail, or check if it is related to power, sound, or overheating."
            ),
        }


# Create instance
get_troubleshooting_steps_tool = GetTroubleshootingStepsTool()