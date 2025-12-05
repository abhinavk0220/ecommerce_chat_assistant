# backend/test_returns_tool.py

from backend.tools.returns_tool import check_return_eligibility_tool


def main():
    # Assume today's date (you can adjust)
    today = "2025-12-05"

    print("Test 1: Delivered order within/around window (ORD1001)")
    res1 = check_return_eligibility_tool.invoke(
        {
            "order_id": "ORD1001",
            "today": today,
        }
    )
    print(res1)

    print("\nTest 2: Recently shipped or processing (ORD1003)")
    res2 = check_return_eligibility_tool.invoke(
        {
            "order_id": "ORD1003",
            "today": today,
        }
    )
    print(res2)

    print("\nTest 3: Non-existing order")
    res3 = check_return_eligibility_tool.invoke(
        {
            "order_id": "ORD9999",
            "today": today,
        }
    )
    print(res3)


if __name__ == "__main__":
    main()
