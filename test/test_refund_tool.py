# backend/test_refund_tool.py

from backend.tools.refund_tool import check_refund_possibility_tool


def main():
    today = "2025-12-05"

    print("Test 1: Refund possibility for ORD1001")
    res1 = check_refund_possibility_tool.invoke(
        {"order_id": "ORD1001", "today": today}
    )
    print(res1)

    print("\nTest 2: Refund possibility for ORD1002")
    res2 = check_refund_possibility_tool.invoke(
        {"order_id": "ORD1002", "today": today}
    )
    print(res2)

    print("\nTest 3: Refund possibility for non-existing order")
    res3 = check_refund_possibility_tool.invoke(
        {"order_id": "ORD9999", "today": today}
    )
    print(res3)


if __name__ == "__main__":
    main()
