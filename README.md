# 📚 **Complete System Architecture & Technical Deep Dive**



---

## **1️⃣ Complete Workflow: How a Prompt is Treated**

### **End-to-End Flow Diagram:**

```
┌─────────────────────────────────────────────────────────────────┐
│ USER INPUT: "Show me my orders"                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (index.html)                                           │
│ • Captures user message                                         │
│ • Retrieves session_id from localStorage                        │
│ • Sends POST /chat request                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP POST {user_message, session_id}
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: app.py - FastAPI Endpoint                              │
│                                                                  │
│ Step 1: Session Validation                                      │
│   • Check if session_id exists                                  │
│   • Create anonymous session if none                            │
│   • Get user_id from session (if logged in)                     │
│                                                                  │
│ Step 2: Guardrails (guardrails.py)                             │
│   • Safety check (violence, self-harm)                          │
│   • Inappropriate content (dating, sexual)                      │
│   • Domain check (ecommerce-related?)                           │
│   • ✅ PASS → Continue                                          │
│   • ❌ BLOCK → Return rejection message                         │
│                                                                  │
│ Step 3: Load Conversation History                              │
│   • db.get_conversation_history(session_id, limit=20)          │
│   • Returns last 20 messages from SQLite                        │
│                                                                  │
│ Step 4: Save User Message                                      │
│   • db.add_message(session_id, role="user", content=...)       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR: agent/orchestrator.py                             │
│                                                                  │
│ Step 5: Quick Intent Detection (router.py)                     │
│   • Pattern matching: "my orders" → order_status intent        │
│   • Extract entities: order_id, user_id, category              │
│   • Purpose: Logging & fallback routing                         │
│                                                                  │
│ Step 6: Handle Simple Cases (No Agentic Loop)                  │
│   • Chitchat: "hi", "hello" → Return greeting                  │
│   • Date query: "what's today?" → Return date                  │
│                                                                  │
│ Step 7: Check Authentication Requirement                        │
│   • Is this a PRIVATE_INTENT? (orders, returns, refunds)       │
│   • Is user_id available? → YES → Continue                     │
│                            → NO → Ask for login/user_id        │
│                                                                  │
│ Step 8: AGENTIC LOOP (Main Intelligence)                       │
│   ┌─────────────────────────────────────────────────────┐     │
│   │ A. Configure Gemini with Function Calling           │     │
│   │    • Load GEMINI_API_KEY                            │     │
│   │    • Create GenerativeModel with tool definitions   │     │
│   │                                                      │     │
│   │ B. Build System Prompt                              │     │
│   │    • Include user_id context (if logged in)         │     │
│   │    • List available tools                           │     │
│   │    • Add behavioral guidelines                      │     │
│   │                                                      │     │
│   │ C. Format Conversation History                      │     │
│   │    • Convert DB format → Gemini format              │     │
│   │    • user messages → {"role": "user", ...}          │     │
│   │    • assistant messages → {"role": "model", ...}    │     │
│   │                                                      │     │
│   │ D. Start Agentic Loop (Max 10 iterations)           │     │
│   │    ┌──────────────────────────────────────────┐    │     │
│   │    │ Iteration 1:                             │    │     │
│   │    │ • Send: system_prompt + user_message     │    │     │
│   │    │ • Gemini decides: "I need to find orders"│   │     │
│   │    │ • Returns: function_call(                │    │     │
│   │    │     name="find_orders_by_user_id",       │    │     │
│   │    │     args={"user_id": "U001"}             │    │     │
│   │    │   )                                       │    │     │
│   │    └──────────┬───────────────────────────────┘    │     │
│   │               │                                     │     │
│   │               ▼                                     │     │
│   │    ┌──────────────────────────────────────────┐    │     │
│   │    │ Execute Tool (execute_tool_call)         │    │     │
│   │    │ • Maps tool name → actual function       │    │     │
│   │    │ • Calls find_orders_by_user_id_tool      │    │     │
│   │    │ • Returns: {found: true, orders: [...]}  │    │     │
│   │    └──────────┬───────────────────────────────┘    │     │
│   │               │                                     │     │
│   │               ▼                                     │     │
│   │    ┌──────────────────────────────────────────┐    │     │
│   │    │ Iteration 2:                             │    │     │
│   │    │ • Send function_response to Gemini       │    │     │
│   │    │ • Gemini processes tool result           │    │     │
│   │    │ • Decides: "I have the answer now"       │    │     │
│   │    │ • Returns: text response                 │    │     │
│   │    │   "You have 2 orders: ORD1001..."        │    │     │
│   │    └──────────────────────────────────────────┘    │     │
│   │                                                      │     │
│   │ E. Loop Exits When:                                 │     │
│   │    • Gemini returns text (final answer)             │     │
│   │    • Max 10 iterations reached                      │     │
│   │    • Error occurs                                   │     │
│   └─────────────────────────────────────────────────────┘     │
│                                                                │
│ Step 9: Fallback Handling                                     │
│   • If agentic loop fails → RAG fallback                      │
│   • answer_with_rag(user_message, k=3)                        │
└────────────────────┬───────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ SAVE RESPONSE                                                   │
│ • db.add_message(session_id, role="assistant", content=...)    │
│ • Store in conversation_history table                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ RETURN TO FRONTEND                                              │
│ {                                                               │
│   "answer": "You have 2 orders...",                            │
│   "intent": "order_status",                                    │
│   "route": "gemini:agentic_function_calling",                  │
│   "tool_calls": [{tool: "find_orders_by_user_id", ...}],      │
│   "iterations": 2                                              │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## **2️⃣ Why Gemini Agentic Flow Over LangGraph?**

### **Comparison Table:**

| Criteria | Gemini Function Calling | LangGraph | LangChain ReAct |
|----------|------------------------|-----------|-----------------|
| **Setup Complexity** | ⭐ Simple | ⭐⭐⭐ Complex | ⭐⭐ Medium |
| **Learning Curve** | Easy | Steep | Medium |
| **Control Over Flow** | Medium | High | Medium |
| **Performance** | Fast | Medium | Medium |
| **Debugging** | Easy | Hard | Medium |
| **Token Efficiency** | High | Medium | Medium |
| **Multi-step Support** | ✅ Yes | ✅ Yes | ✅ Yes |
| **State Management** | Built-in | Explicit | Built-in |

### **Why We Chose Gemini:**

**1. Native Integration** ✅
- Already using Gemini 2.0 for main LLM
- Function calling is native feature
- No additional dependencies

**2. Simplicity** ✅
- Less boilerplate code (~100 lines vs 300+ for LangGraph)
- Easier to explain in viva
- Faster development

**3. Performance** ✅
- Direct API calls (no wrapper overhead)
- Optimized for Gemini's architecture
- Lower latency

**4. Token Efficiency** ✅
- Gemini manages context internally
- No need to manually reconstruct state graphs
- Cheaper per request

**5. Reliability** ✅
- Fewer moving parts = fewer bugs
- Google-maintained (stable API)
- Better error handling

### **When Would You Use LangGraph Instead?**

- **Complex workflows** with 20+ steps
- **Human-in-the-loop** approval needed
- **Parallel execution** of tools required
- **Visual debugging** of workflow needed
- **Production systems** with compliance requirements

### **Agentic Behavior Proof:**

**Traditional (Rule-based):**
```python
if "order" in query:
    call get_order_tool()
```

**Our Agentic Approach:**
```python
# LLM DECIDES autonomously:
"User wants orders → I'll call find_orders_by_user_id
 → Got 2 orders → Now I'll format them nicely
 → Done, here's the answer"
```

**Evidence in Logs:**
```
[Agent] Calling tool: find_orders_by_user_id  ← LLM decided this
[Agent] Tool result: {...}
[Agent] Calling tool: check_return_eligibility  ← LLM chained another tool
```

---

## **3️⃣ User Data Storage & Retrieval**

### **Database Schema (SQLite):**

```sql
-- 1. Users Table
users (
    user_id TEXT PRIMARY KEY,     -- U001, U002
    name TEXT,
    email TEXT UNIQUE,
    password_hash TEXT            -- bcrypt hashed
)

-- 2. Sessions Table
sessions (
    session_id TEXT PRIMARY KEY,  -- UUID
    user_id TEXT,                 -- NULL for anonymous
    created_at TIMESTAMP,
    last_active TIMESTAMP,
    is_active BOOLEAN
)

-- 3. Conversation History
conversation_history (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    user_id TEXT,                 -- Denormalized for queries
    role TEXT,                    -- 'user' or 'assistant'
    content TEXT,
    intent TEXT,
    route TEXT,
    timestamp TIMESTAMP
)

-- 4. Conversation State (for multi-step flows)
conversation_state (
    session_id TEXT PRIMARY KEY,
    current_intent TEXT,
    awaiting_field TEXT,
    collected_slots TEXT          -- JSON
)
```

### **Data Flow:**

**Login Flow:**
```python
# 1. User submits login
POST /login {email: "abhinav@example.com", password: "demo123"}

# 2. Backend validates
user = db.get_user_by_email(email)
verify_password(password, user.password_hash)  # bcrypt

# 3. Create session
session_id = db.create_session(user_id="U001")

# 4. Return to frontend
return {session_id: "abc-123", user_id: "U001", name: "Abhinav"}

# 5. Frontend stores
localStorage.setItem("session_id", "abc-123")
localStorage.setItem("current_user", JSON.stringify({...}))
```

**Session Validation on Each Request:**
```python
# In app.py - chat endpoint
session_id = payload.session_id
user_id = get_session_user(session_id)  # Query DB

# database/db_manager.py
def get_session_user(session_id):
    session = db.execute(
        "SELECT user_id FROM sessions WHERE session_id=? AND is_active=TRUE",
        (session_id,)
    )
    return session.user_id if session else None
```

### **Order Data Retrieval:**

```python
# Structured data: data/structured/orders.json
[
  {
    "order_id": "ORD1001",
    "user_id": "U001",  ← Linked to user
    "items": [...],
    "order_date": "2025-11-20",
    "status": "delivered"
  }
]

# Tool: tools/user_tool.py
def find_orders_by_user_id(user_id):
    orders = load_orders()  # Read JSON
    return [o for o in orders if o["user_id"] == user_id]
```

---

## **4️⃣ Context Preservation**

### **Three Levels of Context:**

#### **Level 1: Session Context (Database)**
```python
# Every message stored in DB
db.add_message(
    session_id="abc-123",
    role="user",
    content="Show my orders"
)
db.add_message(
    session_id="abc-123",
    role="assistant",
    content="You have 2 orders..."
)

# Retrieved on next request
history = db.get_conversation_history(session_id, limit=20)
# Returns last 20 messages in chronological order
```

#### **Level 2: In-Memory Context (Current Request)**
```python
# Format for Gemini
formatted_history = [
    {"role": "user", "parts": [{"text": "Show my orders"}]},
    {"role": "model", "parts": [{"text": "You have 2 orders..."}]},
    {"role": "user", "parts": [{"text": "Return the laptop"}]}
]

# Sent to Gemini
chat = model.start_chat(history=formatted_history)
response = chat.send_message(new_message)
```

#### **Level 3: User Identity Context**
```python
# Injected into system prompt
system_prompt = f"""
User is logged in as: {user_id}
When user says "my orders", use user_id automatically.
"""
```

### **Context Preservation Example:**

**Turn 1:**
```
User: "Show my orders"
History: []
Agent: [Calls find_orders_by_user_id(U001)]
Response: "You have 2 orders: ORD1001, ORD1002"
DB: Saves both messages
```

**Turn 2:**
```
User: "Return the laptop"
History: [Turn 1 messages]
Agent: "Laptop is in ORD1001, checking return eligibility..."
       [Calls check_return_eligibility(ORD1001)]
Response: "ORD1001 is outside return window"
DB: Saves both messages
```

**Turn 3:**
```
User: "What about refund?"
History: [Turn 1, Turn 2 messages]
Agent: "User wants refund for ORD1001 (from context)"
       [Calls check_refund_possibility(ORD1001)]
```

---

## **5️⃣ Session Memory**

### **Storage Location:**
```
data/assistant.db (SQLite file)
```

### **How It Works:**

**1. Session Creation:**
```python
# When user opens chat (no login)
session_id = str(uuid.uuid4())  # "abc-123-def-456"
db.execute("INSERT INTO sessions (session_id, user_id) VALUES (?, NULL)")

# When user logs in
db.execute("UPDATE sessions SET user_id = ? WHERE session_id = ?", (user_id, session_id))
```

**2. Message Storage:**
```python
# After every chat turn
db.execute("""
    INSERT INTO conversation_history (session_id, user_id, role, content)
    VALUES (?, ?, ?, ?)
""", (session_id, user_id, role, content))
```

**3. Message Retrieval:**
```python
# Before processing new message
cursor = db.execute("""
    SELECT role, content FROM conversation_history
    WHERE session_id = ?
    ORDER BY timestamp DESC
    LIMIT 20
""", (session_id,))

history = list(reversed(cursor.fetchall()))  # Chronological order
```

### **Session Lifecycle:**

```
┌─────────────────┐
│ User Opens Chat │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Create Anonymous Session│  session_id = uuid4()
│ Store in localStorage   │  user_id = NULL
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│ User Logs In    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Link Session to User    │  UPDATE sessions SET user_id = "U001"
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ User Chats (5 messages) │  All saved to conversation_history
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│ User Closes Tab │  Session remains in DB
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ User Returns Next Day   │  session_id still in localStorage
│ Context Restored!       │  Load last 20 messages from DB
└─────────────────────────┘
```

### **Memory Limits:**

- **Per Session:** Last 20 messages (configurable)
- **Token Limit:** ~30k tokens (Gemini 2.0 context window)
- **Database:** Unlimited (until disk space)

### **Why Last 20 Messages?**

- **Balance:** Enough context without overwhelming LLM
- **Performance:** Fast retrieval from DB
- **Token Efficiency:** ~5k-10k tokens average
- **Relevance:** Recent messages most important

---

## **6️⃣ How RAG Comes Into Picture**

### **RAG Architecture:**

```
┌───────────────────────────────────────────────────────────┐
│ RAG KNOWLEDGE BASE                                        │
│                                                            │
│ 1. Raw Documents (data/raw/)                              │
│    • return_policy.txt                                    │
│    • shipping_policy.txt                                  │
│    • warranty_terms.txt                                   │
│    • general_faq.txt                                      │
│                                                            │
│ 2. Chunking (rag/chunking.py)                            │
│    • Chunk size: 1000 characters                          │
│    • Overlap: 200 characters                              │
│    • Result: 15-20 chunks                                 │
│                                                            │
│ 3. Embedding (rag/embeddings.py)                         │
│    • Model: all-MiniLM-L6-v2                             │
│    • Dimension: 384                                       │
│    • Speed: ~5ms per chunk                                │
│                                                            │
│ 4. Vector Store (rag/vectorstore.py)                     │
│    • ChromaDB (persistent)                                │
│    • Location: data/vectorstore/                          │
│    • Similarity: Cosine                                   │
└───────────────────────────────────────────────────────────┘
```

### **When RAG is Used:**

**Scenario 1: Policy Questions**
```python
User: "What is your return policy?"

# Orchestrator detects: policy_question intent
# OR: Agentic loop calls search_policy_docs tool

# RAG Pipeline:
1. Embed query → [0.23, -0.45, 0.78, ...]  (384 dims)
2. Search ChromaDB → Top 3 similar chunks
3. Retrieved chunks:
   - Chunk 1: "Return policy allows 7 days..." (similarity: 0.92)
   - Chunk 2: "Electronics can be returned..." (similarity: 0.85)
   - Chunk 3: "Refund processed within 5-7..." (similarity: 0.78)
4. Build prompt:
   Context: [Chunk 1 + Chunk 2 + Chunk 3]
   Question: "What is your return policy?"
5. Send to Gemini → Generate answer
```

**Scenario 2: Troubleshooting (3-Tier)**
```python
User: "My laptop screen is flickering"

Tier 1: Structured tool (troubleshooting.json)
  → Not found (no entry for "flickering")

Tier 2: RAG (search manuals)
  → Search vectorstore for "laptop screen flickering"
  → Found relevant chunks → Return answer

Tier 3: LLM Generic (if RAG fails)
  → Generate general troubleshooting steps
```

### **RAG Flow Diagram:**

```
User Query: "What is warranty period?"
         ↓
    Embed Query
         ↓
┌────────────────────┐
│  Vector Search     │
│  ChromaDB          │
│  Cosine Similarity │
└────────┬───────────┘
         │
         ▼
Retrieved Chunks (Top 3):
┌──────────────────────────────────────┐
│ [Doc 1] "Laptops have 1 year..."     │
│ [Doc 2] "Headphones have 6 months..." │
│ [Doc 3] "Warranty starts from..."    │
└────────┬─────────────────────────────┘
         │
         ▼
Build RAG Prompt:
┌──────────────────────────────────────┐
│ You are an assistant.                │
│ Use ONLY the following context:      │
│                                      │
│ [Doc 1] Laptops have 1 year...      │
│ [Doc 2] Headphones have 6 months... │
│ [Doc 3] Warranty starts from...     │
│                                      │
│ User question:                       │
│ "What is warranty period?"           │
│                                      │
│ Answer based ONLY on context above.  │
└────────┬─────────────────────────────┘
         │
         ▼
    Send to Gemini
         ↓
    Generate Answer
         ↓
"Laptops have a 1-year warranty, while 
 headphones have a 6-month warranty from 
 the date of delivery. [Doc 1][Doc 2]"
```

---

## **7️⃣ RAG + Agentic + LLM: Individual & Combined Working**

### **Individual Components:**

#### **A. LLM (Gemini 2.0) - Brain**
**Role:** Language understanding & generation

**Capabilities:**
- Understand natural language
- Generate coherent responses
- Follow instructions
- Reason about context

**Limitations:**
- ❌ No real-time data
- ❌ Can't access databases
- ❌ Can't execute actions
- ❌ Knowledge cutoff (Jan 2025)

#### **B. RAG (Retrieval-Augmented Generation) - Memory**
**Role:** Provide grounded, factual information

**Capabilities:**
- ✅ Access company policies
- ✅ Retrieve product manuals
- ✅ Find FAQs
- ✅ Ground answers in documents

**Limitations:**
- ❌ Can't handle transactional queries (order status)
- ❌ No user-specific data
- ❌ Static knowledge only

#### **C. Agentic Workflow - Hands**
**Role:** Take actions, use tools

**Capabilities:**
- ✅ Query databases
- ✅ Check order status
- ✅ Calculate return eligibility
- ✅ Chain multiple actions

**Limitations:**
- ❌ Needs LLM to decide what to do
- ❌ Can't generate natural language

### **Combined Power:**

**Example 1: Simple Product Recommendation**
```
User: "Recommend a laptop under 60000"

LLM: "I should use the search_products tool"
     ↓
Agentic: Calls search_products_tool(category="laptop", max_price=60000)
     ↓
Tool Returns: [ZenBook 14, ThinkPro 15]
     ↓
LLM: "Based on the catalog, I recommend ZenBook 14 (₹69,990) 
      and ThinkPro 15 (₹54,990) for your budget..."
```

**Example 2: Policy Question with Context**
```
User: "Can I return my laptop?"

LLM: "I need the user's order first"
     ↓
Agentic: Calls find_orders_by_user_id(U001)
     ↓
Tool Returns: [{order_id: "ORD1001", delivery_date: "2025-11-25"}]
     ↓
Agentic: Calls check_return_eligibility(ORD1001, today="2025-12-07")
     ↓
Tool Returns: {eligible: false, reason: "Outside 7-day window"}
     ↓
LLM: "I should check the policy for exceptions"
     ↓
RAG: Search "return policy exceptions"
     ↓
RAG Returns: "No exceptions for electronics after 7 days"
     ↓
LLM: "Your laptop order ORD1001 was delivered on Nov 25, which 
      is 12 days ago. Unfortunately, our return policy only 
      allows returns within 7 days of delivery, with no 
      exceptions for electronics."
```

**Example 3: Complex Troubleshooting**
```
User: "My laptop is overheating and making noise"

LLM: "This is a troubleshooting query"
     ↓
Agentic: Calls get_troubleshooting_steps("laptop", "overheating")
     ↓
Tool Returns: [
  "Ensure vents are not blocked",
  "Clean dust from vents",
  "Close heavy applications"
]
     ↓
LLM: "The structured steps don't mention noise, let me search docs"
     ↓
RAG: Search "laptop noise overheating"
     ↓
RAG Returns: Chunks about fan maintenance
     ↓
LLM: Synthesizes both sources:
     "For overheating:
      1. Ensure vents are not blocked
      2. Clean dust from vents
      3. Close heavy applications
      
      For the noise:
      The fan might be clogged with dust or failing. Try 
      cleaning the vents first. If noise persists, the fan 
      may need replacement - please contact support."
```

---

## **8️⃣ Guardrails: How They Work**

### **Architecture:**

```
User Input
    ↓
┌────────────────────────────────────┐
│ GUARDRAILS (guardrails.py)        │
│                                    │
│ 1. Empty Check                     │
│    if not text: BLOCK              │
│                                    │
│ 2. Safety Filter                   │
│    keywords: ["suicide", "bomb"]   │
│    if match: BLOCK                 │
│                                    │
│ 3. Inappropriate Content           │
│    keywords: ["date a girl",       │
│               "pickup line"]       │
│    if match: BLOCK                 │
│                                    │
│ 4. Domain Check                    │
│    if not (ecommerce OR chitchat): │
│       BLOCK                         │
│                                    │
│ ✅ PASS → Continue to orchestrator │
│ ❌ BLOCK → Return rejection msg    │
└────────────────────────────────────┘
```

### **Implementation:**

```python
# guardrails.py

BLOCKED_KEYWORDS = [
    "suicide", "kill myself", "bomb", "terrorist"
]

DATING_KEYWORDS = [
    "date a girl", "pickup line", "flirt with"
]

ECOMMERCE_KEYWORDS = [
    "order", "return", "refund", "product", "laptop"
]

CHITCHAT_KEYWORDS = [
    "hi", "hello", "how are you"
]

def apply_guardrails(user_message: str) -> GuardrailResult:
    lowered = user_message.lower()
    
    # Safety
    if any(kw in lowered for kw in BLOCKED_KEYWORDS):
        return GuardrailResult(
            allowed=False,
            reason="safety",
            message="I can't help with that. Please contact emergency services."
        )
    
    # Inappropriate
    if any(kw in lowered for kw in DATING_KEYWORDS):
        return GuardrailResult(
            allowed=False,
            reason="inappropriate",
            message="I'm designed for ecommerce support only."
        )
    
    # Domain
    has_ecommerce = any(kw in lowered for kw in ECOMMERCE_KEYWORDS)
    has_chitchat = any(kw in lowered for kw in CHITCHAT_KEYWORDS)
    
    if not (has_ecommerce or has_chitchat):
        return GuardrailResult(
            allowed=False,
            reason="out_of_domain",
            message="Please ask questions about orders, products, or support."
        )
    
    return GuardrailResult(allowed=True)
```

### **Guardrail Statistics:**

| Category | Example | Action |
|----------|---------|--------|
| Safety | "how to make a bomb" | ❌ BLOCK |
| Inappropriate | "give me pickup lines" | ❌ BLOCK |
| Out of Domain | "tell me a joke" | ❌ BLOCK (unless chitchat detected) |
| Empty | "" | ❌ BLOCK |
| Valid Ecommerce | "show my orders" | ✅ PASS |
| Valid Chitchat | "hello" | ✅ PASS |

---

## **9️⃣ Retrieval Strategy**

### **Retrieval Method: Semantic Similarity (Cosine)**

**Formula:**
```
similarity = (vector_A · vector_B) / (||vector_A|| × ||vector_B||)

Range: [-1, 1]
- 1.0 = Identical
- 0.0 = Orthogonal (unrelated)
- -1.0 = Opposite
```

### **Retrieval Parameters:**

```python
# In rag_chain.py
def answer_with_rag(question: str, k: int = 3):
    retriever = vectordb.as_retriever(
        search_kwargs={
            "k": 3  # Top 3 most similar chunks
        }
    )
```

**Why k=3?**
- ✅ Enough context (3 chunks × 1000 chars = 3000 chars)
- ✅ Manageable token count (~750 tokens)
- ✅ Diverse perspectives
- ✅ Reduces noise

### **Retrieval Pipeline:**

```
1. Query: "What is return policy?"
   ↓
2. Embed: [0.23, -0.45, 0.78, ..., 0.12]  (384 dimensions)
   ↓
3. Search ChromaDB:
   ┌─────────────────────────────────────┐
   │ Chunk 1: "Return policy states..." │ 0.92
   │ Chunk 2: "Electronics can be..."   │ 0.85
   │ Chunk 3: "Refunds processed in..."  │ 0.78
   │ Chunk 4: "Shipping takes 3-5..."    │ 0.45 ← Not retrieved
   └─────────────────────────────────────┘
   ↓
4. Return Top 3
```

### **Retrieval Evaluation Metrics:**

**Recall@k:**
```
Recall@3 = (Relevant docs retrieved) / (Total relevant docs)

Example:
- Relevant docs in DB: 4
- Retrieved: 3
- Recall@3 = 3/4 = 0.75 (75%)
```

**Precision@k:**
```
Precision@3 = (Relevant docs retrieved) / (Docs retrieved)

Example:
- Retrieved: 3
- Relevant: 3
- Precision@3 = 3/3 = 1.0 (100%)
```

---

## **🔟 Tokenization Strategy**

### **Two Levels of Tokenization:**

#### **Level 1: Document Chunking (Character-based)**
```python
# In rag/chunking.py
RecursiveCharacterTextSplitter(
    chunk_size=1000,      # characters
    chunk_overlap=200,    # characters
    length_function=len   # character count
)
```

**Why Character-based?**
- ✅ Simple and predictable
- ✅ Language-agnostic
- ✅ Fast
- ⚠️ Approximates 250-300 words per chunk

#### **Level 2: LLM Tokenization (Gemini BPE)**

**Gemini uses Byte-Pair Encoding (BPE):**
```
Text: "Show me my orders"

Tokenization:
["Show", " me", " my", " orders"]
→ [12345, 67890, 11223, 44556]

Token count: 4
```

### **Token Limits:**

| Component | Limit | Typical Usage |
|-----------|-------|---------------|
| **Gemini Input** | 32,768 tokens | 5,000-10,000 |
| **Gemini Output** | 8,192 tokens | 500-1,500 |
| **Single Chunk** | ~250 tokens | (1000 chars) |
| **History (20 msgs)** | ~5,000 tokens | Variable |
| **System Prompt** | ~500 tokens | Fixed |
| **Tool Definitions** | ~1,000 tokens | Fixed |
| **Total per Request** | ~8,000 tokens | Safe margin |

### **Token Budget Breakdown:**

```
Typical Request:
┌────────────────────────────┬────────┐
│ System Prompt              │   500  │
│ Tool Definitions (8 tools) │ 1,000  │
│ Conversation History (20)  │ 5,000  │
│ User Message               │   100  │
│ RAG Context (3 chunks)     │   750  │
│ Tool Results               │   500  │
├────────────────────────────┼────────┤
│ TOTAL INPUT                │ 7,850  │
└────────────────────────────┴────────┘

Response:
┌────────────────────────────┬────────┐
│ Assistant Message          │   500  │
│ Function Calls (metadata)  │   200  │
├────────────────────────────┼────────┤
│ TOTAL OUTPUT               │   700  │
└────────────────────────────┴────────┘

GRAND TOTAL: 8,550 tokens (well under 32k limit)
```

---

## **1️⃣1️⃣ LLM Calls per Cycle**

### **Scenario Analysis:**

#### **Scenario 1: Simple Chitchat**
```
User: "Hello"
└─ 1 LLM call (direct response)

Total: 1 call
```

#### **Scenario 2: Product Search**
```
User: "Show laptops under 60000"
├─ Call 1: Gemini decides to use search_products tool
├─ [Tool execution - not an LLM call]
└─ Call 2: Gemini formats results into response

Total: 2 calls
```

#### **Scenario 3: Multi-step (Logged in)**
```
User: "I want to return my laptop"
├─ Call 1: Gemini decides to find user's orders
├─ [Tool: find_orders_by_user_id]
├─ Call 2: Gemini processes order list, decides to check eligibility
├─ [Tool: check_return_eligibility]
└─ Call 3: Gemini formats final answer

Total: 3 calls
```

#### **Scenario 4: Complex with RAG**
```
User: "My laptop is overheating, can I return it?"
├─ Call 1: Gemini finds user orders
├─ [Tool: find_orders_by_user_id]
├─ Call 2: Gemini checks return eligibility
├─ [Tool: check_return_eligibility]
├─ Call 3: Gemini searches troubleshooting
├─ [Tool: get_troubleshooting_steps]
├─ Call 4: Gemini searches policy docs (RAG)
│   ├─ [RAG retrieval - not an LLM call]
│   └─ Call 5: RAG's answer_with_rag() calls Gemini
└─ Call 6: Gemini synthesizes everything

Total: 6 calls
```

### **Average Statistics:**

| Query Type | Avg Iterations | Avg LLM Calls | Avg Tools Used |
|------------|----------------|---------------|----------------|
| Chitchat | 1 | 1 | 0 |
| Product Search | 2 | 2 | 1 |
| Order Status | 2 | 2 | 1-2 |
| Return/Refund | 3 | 3 | 2-3 |
| Complex Multi-step | 4-5 | 5-6 | 3-5 |

### **Max Iterations Safety:**

```python
# In orchestrator.py
for iteration in range(10):  # MAX 10 to prevent infinite loops
    ...
```

**Why 10?**
- ✅ Handles 99% of queries (most need 2-4)
- ✅ Prevents runaway costs
- ✅ Timeout protection
- ✅ User experience (fast responses)

---

## **1️⃣2️⃣ Scenario-Based Questions for Viva**

### **Q1: What if ChromaDB goes down?**
**A:** Fallback mechanism:
1. Try RAG first
2. If fails, use LLM's parametric knowledge
3. If LLM uncertain, return: "I need to check our documentation. Please contact support."

### **Q2: How do you handle concurrent users?**
**A:** 
- SQLite supports concurrent reads
- Each session is isolated (session_id)
- No shared state between users
- Can scale to ~100 concurrent users
- For production: Migrate to PostgreSQL + Redis

### **Q3: What if user clears browser data?**
**A:**
- Loses session_id from localStorage
- New anonymous session created
- Previous history lost (unless logged in)
- If logged in: Can create new session with same user_id

### **Q4: How do you prevent prompt injection?**
**A:**
1. Guardrails filter malicious inputs
2. System prompts have clear boundaries
3. Tools are sandboxed (can't execute arbitrary code)
4. No `eval()` or dynamic code execution
5. User input never becomes code

### **Q5: What's your token cost per query?**
**A:**
```
Gemini 2.0 Flash Pricing:
- Input: $0.10 / 1M tokens
- Output: $0.30 / 1M tokens

Average query:
- Input: 8,000 tokens = $0.0008
- Output: 700 tokens = $0.00021
- Total: $0.001 per query

1000 queries = $1
```

### **Q6: How would you add a new tool?**
**A:**
```python
# Step 1: Define in tool_definitions.py
{
    "name": "cancel_order",
    "description": "Cancel an order",
    "parameters": {...}
}

# Step 2: Implement in tools/
def cancel_order_tool(order_id):
    ...

# Step 3: Add to orchestrator.py execute_tool_call()
tool_map = {
    ...
    "cancel_order": cancel_order_tool
}
```

### **Q7: How do you evaluate RAG quality?**
**A:**
- **Retrieval Eval:** Recall@3, Precision@3
- **Generation Eval:** ROUGE-L (overlap with ground truth)
- **Human Eval:** Accuracy, Helpfulness, Relevance
- See `retrieval_eval.py` and `generation_eval.py`

### **Q8: Why SQLite instead of PostgreSQL?**
**A:**
- ✅ Zero setup (file-based)
- ✅ Perfect for demo/capstone
- ✅ Handles 100s of users
- ✅ Easy to show evaluators
- ⚠️ Production: Would use PostgreSQL

### **Q9: What if Gemini API rate limits you?**
**A:**
- Implement exponential backoff
- Queue requests
- Fallback to cached responses
- Show user: "High traffic, please wait..."

### **Q10: How would you add voice input?**
**A:**
```javascript
// Frontend
navigator.mediaDevices.getUserMedia({audio: true})
  .then(stream => {
    const recognition = new webkitSpeechRecognition();
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      sendMessage(transcript);
    };
  });
```

---

## **🎯 Quick Reference Card for Viva**

```
┌─────────────────────────────────────────────────────────┐
│ SYSTEM OVERVIEW                                         │
├─────────────────────────────────────────────────────────┤
│ Architecture: RAG + Agentic + Tools + Guardrails       │
│ LLM: Gemini 2.0 Flash Experimental                     │
│ Vector DB: ChromaDB (Chroma)                           │
│ Embedding: all-MiniLM-L6-v2 (384 dims)                 │
│ Database: SQLite (assistant.db)                        │
│ Framework: FastAPI + Vanilla JS                        │
│ Agent Pattern: Gemini Function Calling (ReAct-style)   │
│                                                          │
│ KEY METRICS                                             │
├─────────────────────────────────────────────────────────┤
│ Chunk Size: 1000 chars (overlap 200)                   │
│ Retrieval: Top-3 (Cosine similarity)                   │
│ History: Last 20 messages                              │
│ Max Iterations: 10 per query                           │
│ Avg LLM Calls: 2-3 per query                           │
│ Tokens/Query: ~8k input, ~700 output                   │
│ Response Time: 2-5 seconds                             │
│                                                          │
│ AGENTIC PROOF                                           │
├─────────────────────────────────────────────────────────┤
│ ✅ LLM autonomously decides which tools to call         │
│ ✅ Can chain 3-5 tools in sequence                      │
│ ✅ Self-corrects based on tool results                  │
│ ✅ Adapts strategy mid-conversation                     │
│                                                          │
│ PRODUCTION READINESS                                    │
├─────────────────────────────────────────────────────────┤
│ ✅ Authentication & Authorization                        │
│ ✅ Session Management                                    │
│ ✅ Conversation Memory                                   │
│ ✅ Error Handling & Fallbacks                           │
│ ✅ Guardrails (Safety, Domain, Inappropriate)          │
│ ⚠️  Would add: Rate limiting, Caching, Monitoring      │
└─────────────────────────────────────────────────────────┘
```

---

**Good luck! You've built a production-quality system!** 🚀
