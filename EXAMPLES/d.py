from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Ecommerce Support Assistant - Technical Documentation', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def clean_text(self, text):
        """
        Cleans text to remove emojis and unsupported characters
        to prevent UnicodeEncodeError in standard PDF generation.
        """
        replacements = {
            # Arrows & Shapes
            '\u2193': 'v', '\u2191': '^', '\u2192': '->', '\u2190': '<-',
            '\u25bc': 'v', '\u25b2': '^', 
            '\u250c': '+', '\u2510': '+', '\u2514': '+', '\u2518': '+',
            '\u2500': '-', '\u2502': '|', '\u251c': '+', '\u2524': '+',
            '\u2534': '+', '\u252c': '+', '\u253c': '+',
            # Punctuation
            '\u2013': '-', '\u2014': '--', '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"', '\u2022': '*',
            # Emojis (mapped to text/symbols)
            '🔥': '[!]', '✔': '[OK]', '📌': '[Note]', '🚀': '->', 
            '🏁': '[End]', '✅': '[OK]', '❌': '[X]', '📘': '', '✨': '',
            '🎯': '', '🔧': '[Config]',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
            
        # Final safety encoding
        return text.encode('latin-1', 'ignore').decode('latin-1')

    def chapter_title(self, title):
        title = self.clean_text(title)
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        body = self.clean_text(body)
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, body)
        self.ln()

    def add_code_block(self, code):
        code = self.clean_text(code)
        self.set_font('Courier', '', 9)
        self.set_fill_color(245, 245, 245)
        self.multi_cell(0, 5, code, 0, 'L', True)
        self.ln()
        self.set_font('Arial', '', 11)

    def add_image_centered(self, image_path, caption):
        caption = self.clean_text(caption)
        if os.path.exists(image_path):
            self.ln(5)
            try:
                # A4 width is 210mm. Margins 10mm. Image max width 180mm.
                self.image(image_path, x=15, w=180) 
            except Exception as e:
                self.set_text_color(255, 0, 0)
                self.cell(0, 10, f"Error loading image: {str(e)}", 0, 1)
                self.set_text_color(0, 0, 0)
                return

            self.ln(2)
            self.set_font('Arial', 'I', 9)
            self.cell(0, 5, caption, 0, 1, 'C')
            self.ln(5)
            self.set_font('Arial', '', 11)
        else:
            self.set_text_color(255, 0, 0)
            self.cell(0, 10, f"Error: Image {image_path} not found.", 0, 1)
            self.set_text_color(0, 0, 0)

# --- Main PDF Generation ---

pdf = PDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# --- Title Page ---
pdf.set_font('Arial', 'B', 24)
pdf.ln(50)
pdf.cell(0, 10, 'AI-Powered Ecommerce', 0, 1, 'C')
pdf.cell(0, 10, 'Support Assistant', 0, 1, 'C')
pdf.ln(10)
pdf.set_font('Arial', '', 14)
pdf.cell(0, 10, 'Technical Design & Architecture', 0, 1, 'C')
pdf.ln(20)
pdf.set_font('Arial', '', 12)
pdf.cell(0, 10, 'Project Documentation & Evaluation', 0, 1, 'C')
pdf.add_page()

# --- 1. Overview ---
pdf.chapter_title('1. Overview')
pdf.chapter_body(
    "This document describes the design, architecture, and evaluation of an AI-powered Ecommerce Support Assistant. "
    "The system combines Retrieval-Augmented Generation (RAG), an agentic workflow with intent-based routing, "
    "deterministic tools (orders, returns, refunds, warranty, products, troubleshooting), guardrails for safety, "
    "and in-memory caching for performance.\n\n"
    "The assistant acts as a smart support layer for an ecommerce platform, handling queries about order status, "
    "returns, warranty coverage, product discovery, and troubleshooting."
)

# --- 2. System Goals ---
pdf.chapter_title('2. System Goals')
pdf.chapter_body(
    "2.1 Functional Goals:\n"
    "* Support transaction-like queries (orders, returns, warranty).\n"
    "* Make product suggestions using structured catalog data.\n"
    "* Provide troubleshooting steps and answer policy FAQs.\n\n"
    "2.2 Non-Functional Goals:\n"
    "* Low hallucination: Answers grounded in policies/tools.\n"
    "* Safety: Guardrails preventing harmful content.\n"
    "* Performance: In-memory caching for rapid responses."
)

# --- 3. Tech Stack ---
pdf.chapter_title('3. Tech Stack')
pdf.chapter_body(
    "* Backend: FastAPI (Async Python framework).\n"
    "* LLM: Gemini 2.5 Flash (Reasoning and generation).\n"
    "* Embeddings: Sentence Transformers (all-MiniLM-L6-v2).\n"
    "* Vector Store: ChromaDB (Local, file-based).\n"
    "* Orchestration: Custom Router + LangChain."
)

# --- 4. System Workflow Diagrams ---
pdf.chapter_title('4. System Workflow & Architecture')
pdf.chapter_body(
    "The system follows a strict decision flow to ensure accuracy and safety. "
    "Below are the detailed diagrams for the backend and specific query branches."
)

pdf.chapter_body("4.1 High-Level Backend Flow")
diagram_main = """
         +---------------------+
         |   User /chat POST   |
         +---------+-----------+
                   |  raw_message
                   v
        +------------------------+
        |  Guardrails Layer      |
        |  apply_guardrails()    |
        +---------+--------------+
          allowed?|
        +---------+--------------+
        |                        |
        v                        v
+-----------------+      +------------------------------+
| RETURN:         | NO   | Yes: proceed to next layer   |
| guardrail msg   |      +------------------------------+
+-----------------+
                   v
        +------------------------+
        |   Caching Layer        |
        |   (in-memory dict)     |
        +---------+--------------+
          cache hit?|
        +----------+-------------+
        |                        |
        v                        v
+--------------------+  +-------------------------+
| RETURN: cached     |  |  Agent Orchestrator     |
| answer + metadata  |  |  handle_user_message()  |
+--------------------+  +---------+---------------+
                                   |
                                   v
                        +-----------------------+
                        |  Router: detect_intent|
                        +---------+-------------+
                                  |
                      +-----------+---------------------------------------------+
                      |           |                     |                       |
                      v           v                     v                       v
              order/return/    product_search     troubleshooting         policy/general
              refund/warranty      intent            intent                RAG intent
              intents
"""
pdf.add_code_block(diagram_main)

pdf.add_page()
pdf.chapter_body("4.2 Branch 1: Tool-based Queries (Orders/Returns/Warranty)")
pdf.chapter_body("These queries are handled deterministically using pure Python logic on JSON data.")
diagram_branch1 = """
Intent IN {order_status, return_eligibility, refund, warranty_status}
        |
        v
+----------------------------+
| Call corresponding tool:   |
|   - get_order_status_tool  |
|   - check_return_eligibility_tool
|   - check_refund_possibility_tool
|   - check_warranty_status_tool
+---------+------------------+
          |  (Python logic on JSON data)
          v
  Build natural language answer -> Save result in cache -> RETURN
"""
pdf.add_code_block(diagram_branch1)

pdf.chapter_body("4.3 Branch 2: Product Search (Tools + LLM)")
pdf.chapter_body("A hybrid approach: Tools filter the catalog, and the LLM phrases the recommendation.")
diagram_branch2 = """
Intent == product_search
        |
        v
+------------------------------------+
| Tool: search_products_tool.invoke |
|   - Filter by category, max_price |
|   - Filter by tags                |
+---------+--------------------------+
          |
          v
+--------------------------------------------+
| LLM (Gemini via get_llm)                  |
| Prompt:                                   |
|  - "Here are products from catalog..."    |
|  - Explain, compare, recommend            |
+---------+----------------------------------+
          |
          v
   Final recommended answer -> Cache -> Return
"""
pdf.add_code_block(diagram_branch2)

pdf.chapter_body("4.4 Branch 3: Troubleshooting (Tool-First, RAG-Second)")
diagram_branch3 = """
Intent == troubleshooting
        |
        v
+-------------------------------------+
| Tool: get_troubleshooting_steps_tool |
|   - Normalize product_type          |
|   - Infer issue_key                 |
+---------+---------------------------+
          |
          | steps found?
          +------------- Yes ---------------> Return tool message (no RAG)
          |
          v
        No
          |
          v
+----------------------------------------+
| Fallback to RAG: answer_with_rag()    |
|   - Retrieve from manuals/policies    |
|   - LLM (Gemini) generates answer     |
+---------+------------------------------+
"""
pdf.add_code_block(diagram_branch3)

pdf.chapter_body("4.5 Branch 4: Policy & FAQ (RAG-Only)")
diagram_branch4 = """
Intent IN {policy_question, general_rag}
        |
        v
+----------------------------+
| RAG: answer_with_rag()     |
|   1. Embed query           |
|   2. Chroma similarity     |
|   3. Retrieve top-k chunks |
|   4. Prompt Gemini         |
+----------------------------+
"""
pdf.add_code_block(diagram_branch4)

# --- 5. Screenshots ---
pdf.add_page()
pdf.chapter_title('5. User Interface & Capabilities')

pdf.chapter_body("5.1 Order Tracking & Greeting")
pdf.add_image_centered('d1.png', 'Figure 1: Greeting, Order Tracking, and Search Intents')

pdf.chapter_body("5.2 Product Recommendations & Troubleshooting")
pdf.add_image_centered('d2.png', 'Figure 2: Product Suggestion and Troubleshooting Flow')

pdf.chapter_body("5.3 RAG Support & Guardrails")
pdf.add_image_centered('d3.png', 'Figure 3: Policy RAG and Guardrail Blocking')

# --- 6. Evaluation (NEW DETAILED SECTION) ---
pdf.add_page()
pdf.chapter_title('6. Evaluation')
pdf.chapter_body("We performed a structured evaluation on 10 queries across policy retrieval, tool-based logic, and troubleshooting.")

pdf.chapter_body("6.1 Retrieval Evaluation Results")
retrieval_table = """
Metric               | Score          | Remark
---------------------|----------------|-------------------------------------
Average Recall@k     | 1.00 (100%)    | Perfect document retrieval
Average Precision@k  | 0.57 (57%)     | Some extra chunks retrieved (expected)
"""
pdf.add_code_block(retrieval_table)
pdf.chapter_body(
    "Interpretation: The system achieved Perfect Recall, meaning the relevant reference document "
    "was always retrieved within the Top-3 results. Precision is moderate due to the inclusion "
    "of adjacent context chunks, which is typical for small vector stores."
)

pdf.chapter_body("6.2 Answer Quality Evaluation Results")
quality_table = """
Metric               | Score   | Remark
---------------------|---------|-------------------------------------
Routing Accuracy     | 90%     | Strong agent workflow
Hallucination Rate   | 10%     | Good safety behavior
ROUGE-L F1           | 0.24    | Answers factually correct but vary in phrasing
"""
pdf.add_code_block(quality_table)
pdf.chapter_body(
    "Interpretation: Routing is very strong (9/10 correct). Hallucinations are low due to "
    "tool-first logic. The ROUGE score reflects that while the answers are correct, the LLM "
    "often generates more natural/verbose responses than the ground truth references."
)

pdf.add_page()
pdf.chapter_body("6.3 Insights per Query Type")
insights_table = """
Query Type                  | Performance | Notes
----------------------------|-------------|-----------------------------
Policy & Company FAQs       | Very High   | RAG works accurately
Order/Return/Warranty       | Perfect     | Tools are 100% deterministic
Troubleshooting             | Good        | Structure is good, needs more detail
Product Discovery           | Moderate    | Limited by small demo catalog
"""
pdf.add_code_block(insights_table)

pdf.chapter_body("6.4 Final Evaluation Summary")
pdf.chapter_body(
    "We evaluated the Antigravity AI Commerce Assistant using a structured evaluation set. "
    "Retrieval performance was excellent (100% Recall), ensuring correct knowledge access. "
    "The agent demonstrated 90% routing accuracy, confirming that the intent classifier "
    "successfully activates the correct tool or RAG pipeline.\n\n"
    "Hallucination was low (10%), showing that the safeguards, RAG grounding, and tool-first logic "
    "significantly reduce fabricated responses. Overall, the system delivers reliable ecommerce "
    "support automation with room for further enhancements in product discovery."
)

# --- 7. Future Work ---
pdf.chapter_title('7. Future Improvements')
pdf.chapter_body(
    "1. Reranking: Implement LLM scoring to boost Precision@k.\n"
    "2. Expanded Catalog: Add more products and attributes to improve recommendations.\n"
    "3. Prompt Reinforcement: Further reduce hallucinations with stricter system prompts.\n"
    "4. Fine-grained Evaluation: Add BERTScore for stronger NLP benchmarking."
)

# --- Output ---
try:
    filename = "Ecommerce_Support_Assistant_Docs.pdf"
    pdf.output(filename)
    print(f"\nSUCCESS! The PDF '{filename}' has been created with full evaluation details.")
except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")