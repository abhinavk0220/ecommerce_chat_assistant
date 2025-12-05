# backend/test_product_tool.py

from tools.product_tool import load_products, search_products_tool


def main():
    print("Loaded products:")
    products = load_products()
    for p in products:
        print(p)

    print("\nTest 1: Laptops under 60000")
    result1 = search_products_tool.invoke(
        {
            "category": "laptop",
            "max_price": 60000,
            "brand": None,
            "required_tags": [],
        }
    )
    print(result1)

    print("\nTest 2: Wireless headphones under 4000")
    result2 = search_products_tool.invoke(
        {
            "category": "headphones",
            "max_price": 4000,
            "required_tags": ["wireless"],
            "brand": None,
        }
    )
    print(result2)


if __name__ == "__main__":
    main()
