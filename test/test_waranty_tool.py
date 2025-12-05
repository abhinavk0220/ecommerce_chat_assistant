# backend/test_warranty_tool.py

from backend.tools.warranty_tool import check_warranty_status_tool


def main():
    today = "2025-12-05"

    print("Test 1: Laptop in ORD1001 (LAP123)")
    res1 = check_warranty_status_tool.invoke(
        {
            "order_id": "ORD1001",
            "product_id": "LAP123",
            "today": today,
        }
    )
    print(res1)

    print("\nTest 2: Headphones in ORD1002 (HPH001)")
    res2 = check_warranty_status_tool.invoke(
        {
            "order_id": "ORD1002",
            "product_id": "HPH001",
            "today": today,
        }
    )
    print(res2)

    print("\nTest 3: Wrong product in order")
    res3 = check_warranty_status_tool.invoke(
        {
            "order_id": "ORD1001",
            "product_id": "HPH001",
            "today": today,
        }
    )
    print(res3)

    print("\nTest 4: Non-existing order")
    res4 = check_warranty_status_tool.invoke(
        {
            "order_id": "ORD9999",
            "product_id": "LAP123",
            "today": today,
        }
    )
    print(res4)


if __name__ == "__main__":
    main()
