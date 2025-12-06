Absolutely — here is the **production-ready GitHub README.md**
You can **copy + paste directly** into your repository 👇

---

# 🛒 AI-Powered Ecommerce Support Assistant

**Retrieval-Augmented + Agentic Workflow + Tools + Guardrails**

A fully functional ecommerce customer support assistant that can:

✔️ Track orders
✔️ Check return/refund eligibility
✔️ Validate warranty
✔️ Suggest products within budget
✔️ Troubleshoot devices (laptops/headphones)
✔️ Answer policy and company-related questions
✔️ Handle follow-up conversation safely using guardrails

---

## ⭐ Key Features

| Category            | Details                                                                    |                   |
| ------------------- | -------------------------------------------------------------------------- | ----------------- |
| **LLM**             | Gemini 2.5 Flash (API-based)                                               |                   |
| **RAG System**      | Sentence-Transformers embeddings + ChromaDB                                |                   |
| **Agentic Routing** | Intelligent intent classification → best execution path                    |                   |
| **Tools**           | Order Status, Returns, Refunds, Warranty, Product Search & Troubleshooting |                   |
| **Guardrails**      | Domain safety filtering (policies-only support)                            |                   |
| **Caching**         | In-Memory cache to speed up repeated queries                               |                   |
| **Backend API**     | FastAPI powered `/chat` endpoint                                           |                   |
| **Evaluation**      | Retrieval Recall@3: 1.00                                                   | Precision@3: 0.57 |

---

## 📁 Project Structure

```
RAG-Assistant-Project/
│
├── backend/
│   ├── app.py                 # FastAPI backend /chat endpoint
│   ├── llm_adapter.py         # Gemini API integration
│   ├── guardrails.py          # Safety rules
│   ├── rag/                   # RAG pipeline
│   │   ├── vectorstore.py
│   │   └── rag_chain.py
│   ├── agent/                 # Agentic orchestration + router
│   │   ├── orchestrator.py
│   │   └── router.py
│   ├── tools/                 # Deterministic business logic
│   │   ├── order_tools.py
│   │   ├── return_tools.py
│   │   ├── warranty_tools.py
│   │   ├── refund_tools.py
│   │   └── troubleshoot_tools.py
│   └── evaluation/            # Eval scripts
│       ├── retrieval_eval.py
│       └── generation_eval.py
│
├── data/
│   ├── raw/                   # Knowledge docs (policy, FAQ, manuals)
│   └── structured/            # Products & orders JSON
│
└── README.md                  # (🤩 You're reading it!)
```

---

## ⚙️ Installation

### 1️⃣ Create Environment (Python 3.11 recommended)

```bash
python -m venv myEnv
source myEnv/bin/activate   # Mac/Linux
myEnv\Scripts\activate      # Windows
```

### 2️⃣ Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3️⃣ Set Your Gemini API Key

Create a `.env` file inside `backend/`:

```
GEMINI_API_KEY=your_api_key_here
```

---

## ▶️ Run the Application

From the **backend** directory:

```bash
uvicorn app:app --reload
```

Server starts at:

👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
(test your `/chat` API interactively)

---

## 💬 Calling the Chat Endpoint

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Where is my order ORD1002?"}'
```

Example response:

```json
{
  "answer": "Order ORD1002 has been shipped...",
  "intent": "order_status",
  "route": "tool:order_status"
}
```

---

## 🧠 RAG Knowledge Base

All policy and support knowledge stored in:

```
data/raw/
```

To re-build the vector database:

```bash
python backend/rag/vectorstore.py
```

---

## 🏗️ Tools Overview

| Tool               | Action                   |
| ------------------ | ------------------------ |
| Order Status       | `/order_tools.py`        |
| Return Eligibility | `/return_tools.py`       |
| Warranty           | `/warranty_tools.py`     |
| Refunds            | `/refund_tools.py`       |
| Troubleshooting    | `/troubleshoot_tools.py` |

Each is triggered automatically using **intent-based routing**.

---

## 🔒 Safety Guardrails

* Blocks harmful / offensive / sexual content
* Redirects irrelevant chat back to ecommerce domain
* Reduces hallucinations by forcing tool or RAG grounding

---

## 📊 Evaluation Summary

| Metric                      | Score          |
| --------------------------- | -------------- |
| **Retrieval Recall@3**      | 1.00 (Perfect) |
| **Retrieval Precision@3**   | 0.57           |
| **Answer Routing Accuracy** | 90%            |
| **Hallucination Rate**      | ~10%           |

Scripts used:

```bash
python backend/evaluation/retrieval_eval.py
python backend/evaluation/generation_eval.py
```

---

## 🛣️ Roadmap

| Feature                              | Status |
| ------------------------------------ | ------ |
| Product catalog expansion            | 🔜     |
| Rich UI (cards, product images, CTA) | 🔜     |
| Redis or persistent caching          | 🔜     |
| Personalized user memory             | 🔜     |
| Admin dashboard for analytics        | 🔜     |

---

## 🏁 Final Notes

This system provides a **production-aligned architecture**:

* Hybrid **agent + tools + RAG** design ✔️
* Business logic grounded in **deterministic tools** ✔️
* Policies and knowledge **fully explainable** ✔️
* Fast and cost-efficient with caching ✔️

Perfect foundation to scale into a **real ecommerce AI assistant**.

---

If you'd like, I can also:

🚀 Deploy this using **Docker** + Render/Railway/Vercel
🌐 Build the polished **frontend chat UI**
📦 Help publish your final **project demo site**

Would you like me to generate a **project poster** or **video presentation script** next?
