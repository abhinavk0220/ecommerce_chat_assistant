from backend.llm_adapter import get_llm

llm = get_llm(provider="gemini")

response = llm.generate_content("Hey! Gemini setup is working. Confirm?")
print(response.text)
