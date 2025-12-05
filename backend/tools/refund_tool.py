# backend/tools/refund_tool.py

"""
Refund tool module.

This tool answers questions like:
- "Can I get a refund for order ORD1001?"
- "When will I get my refund?"

It builds on top of:
- Return eligibility (check_return_eligibility_tool)
- Order data (orders.json)

For demo purposes, we assume:
- Refund is only possible if the order is eligible for return.
- Once the return is approved and item is received, refund is processed
  within 5–7 business days to the original payment method.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

from langchain_core.tools import tool

from tools.returns_tool import check_return_eligibility_tool
from tools.order_tool import find_order_by_id


def _parse_date(date_str: str | None):
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d")


@tool("check_refund_possibility", return_direct=False)
def check_refund_possibility_tool(order_id: str, today: str) -> Dict[str, Any]:
    """
    Check whether a refund is possible for a given order_id, and describe
    the expected refund flow.

    Args:
        order_id: e.g. "ORD1001"
        today: current date in "YYYY-MM-DD" format

    Returns:
        {
          "found": bool,
          "refundable": bool,
          "order_id": str,
          "status": str or None,
          "delivery_date": str or None,
          "reason": str,
          "expected_refund_timeline": str or None,
        }
    """
    # 1) Check return eligibility first
    eligibility = check_return_eligibility_tool.invoke(
        {"order_id": order_id, "today": today}
    )

    if not eligibility.get("found", False):
        # Order itself not found
        return {
            "found": False,
            "refundable": False,
            "order_id": order_id,
            "status": None,
            "delivery_date": None,
            "reason": eligibility.get("reason", f"No order found with ID {order_id}."),
            "expected_refund_timeline": None,
        }

    status = eligibility.get("status")
    delivery_date = eligibility.get("delivery_date")
    eligible = eligibility.get("eligible", False)
    base_reason = eligibility.get("reason", "")

    if not eligible:
        # If not return-eligible, then no refund
        return {
            "found": True,
            "refundable": False,
            "order_id": order_id,
            "status": status,
            "delivery_date": delivery_date,
            "reason": (
                base_reason
                + " Since the order is not eligible for return, a refund cannot be processed."
            ),
            "expected_refund_timeline": None,
        }

    # 2) If eligible → describe refund flow
    #    Demo assumption: refund is processed 5–7 business days after item is received/inspected.
    today_dt = _parse_date(today)
    if today_dt is None:
        refund_timeline = None
    else:
        # Rough estimate: add 7 days as an upper bound
        estimated_refund_date = today_dt + timedelta(days=7)
        refund_timeline = (
            f"If you initiate a return now, the refund will typically be processed "
            f"within 5–7 business days after the returned item is received and inspected. "
            f"Based on today’s date ({today}), you can expect the refund to be completed "
            f"by around {estimated_refund_date.date()}."
        )

    reason = (
        base_reason
        + " Since the order is eligible for return, a refund can be issued to the "
        "original payment method once the return is completed."
    )

    return {
        "found": True,
        "refundable": True,
        "order_id": order_id,
        "status": status,
        "delivery_date": delivery_date,
        "reason": reason,
        "expected_refund_timeline": refund_timeline,
    }
