# backend/test_order_tool.py

from tools.order_tool import load_orders, find_order_by_id, get_order_status_tool


def main():
    print("Loaded orders:")
    orders = load_orders()
    for o in orders:
        print(o)

    print("\nTest: existing order ORD1001")
    result1 = get_order_status_tool.invoke({"order_id": "ORD1001"})
    print(result1)

    print("\nTest: non-existing order ORD9999")
    result2 = get_order_status_tool.invoke({"order_id": "ORD9999"})
    print(result2)


if __name__ == "__main__":
    main()
