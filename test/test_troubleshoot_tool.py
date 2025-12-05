# backend/test_troubleshooting_tool.py

from backend.tools.troubleshooting_tool import get_troubleshooting_steps_tool


def main():
    print("Test 1: Laptop not turning on")
    res1 = get_troubleshooting_steps_tool.invoke(
        {
            "product_type": "laptop",
            "issue": "not turning on",
        }
    )
    print(res1["message"])

    print("\nTest 2: Headphones no sound")
    res2 = get_troubleshooting_steps_tool.invoke(
        {
            "product_type": "headphones",
            "issue": "no sound",
        }
    )
    print(res2["message"])

    print("\nTest 3: Unknown issue")
    res3 = get_troubleshooting_steps_tool.invoke(
        {
            "product_type": "laptop",
            "issue": "screen flickering weirdly",
        }
    )
    print(res3)


if __name__ == "__main__":
    main()
