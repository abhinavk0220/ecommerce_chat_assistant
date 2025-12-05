# backend/test_agent.py

from agent.orchestrator import handle_user_message


def run_case(message: str):
    print("\n" + "="*80)
    print("USER:", message)
    result = handle_user_message(message, today="2025-12-05")
    print("INTENT:", result["intent"])
    print("ROUTE :", result["route"])
    print("\nANSWER:\n", result["answer"])
    print("\nROUTER INFO:", result["router_info"])
    if result["tool_result"] is not None:
        print("\nTOOL RESULT:", result["tool_result"])
    if result["rag_result"] is not None:
        print("\nRAG RESULT (answer + sources):", result["rag_result"].keys())


def main():
    # 1. Order status
    run_case("Where is my order ORD1002?")

    # 2. Return eligibility
    run_case("Can I return my laptop order ORD1001?")

    # 3. Warranty
    run_case("Is my laptop from order ORD1001 still under warranty?")

    # 4. Product search
    run_case("Can you suggest some laptops under 60000 for me?")

    # 5. Policy question (RAG)
    run_case("What is your return policy on headphones?")

    # 6. Troubleshooting (RAG)
    run_case("My device is not turning on. What should I do?")

    # 7. General RAG
    run_case("Do you offer free shipping?")

if __name__ == "__main__":
    main()
