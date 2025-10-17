# 🤖 AI Assistant with Function Tools + Pushover Notifications

This project builds an **interactive AI assistant** that represents a specific person (in this case, *Ypatios Chaniotakos*) and can **take real-world actions** — like recording user interest or saving unanswered questions — by calling external *tools* (functions).  

It also integrates with **Pushover** to send **mobile push notifications** whenever one of these tools is used.

---

## 🚀 Overview

The system is an **agentic AI chatbot** that runs locally with a Gradio chat interface.  

It uses:
- **OpenAI’s function calling (tools)** feature
- **JSON schemas** to describe function arguments
- **Pushover API** to send real-time mobile notifications

---

## 🧠 Architecture Summary

| Component | Purpose |
|------------|----------|
| **OpenAI Chat Model (`gpt-4o-mini`)** | Handles the dialogue and decides when to call tools. |
| **Function Tools** | Let the model execute predefined Python functions (e.g., record user details). |
| **Pushover API** | Sends push notifications when tools are triggered. |
| **Gradio UI** | Provides an interactive chat interface in your browser. |
| **PDF + Summary files** | Provide biographical context for Ypatios Chaniotakos. |

---

## 🔔 Setting Up Pushover

To receive mobile notifications from your assistant:

1. Go to **[https://pushover.net/](https://pushover.net/)**  
   Create a free account and download the Pushover app on your phone (iOS or Android).

2. In your Pushover dashboard, find:
   - **User Key**
   - **API Token / Key**
   - **API Endpoint URL** (usually `https://api.pushover.net/1/messages.json`)

3. Create a `.env` file in the project root with:
   ```bash
   PUSHOVER_USER="your_user_key"
   PUSHOVER_TOKEN="your_api_token"
   PUSHOVER_URL="https://api.pushover.net/1/messages.json"
   OPENAI_API_KEY="your_openai_api_key"
   ```

4. The assistant will now send push notifications every time it:
   - Records a user’s contact details.
   - Logs an unknown or unanswered question.

---

## ⚙️ How Tools Work

OpenAI’s **tools** feature (also known as *function calling*) lets the model **decide when to call real Python functions** — and what arguments to pass.

### 🔩 Defining Tools

Each tool is declared as a JSON schema describing:
- The function’s **name**
- A **description**
- The **parameter structure**

Example:

```python
record_user_details_json = {
    "name": "record_user_details",
    "description": "Record that a user provided contact details.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "name": {"type": "string"},
            "notes": {"type": "string"}
        },
        "required": ["email"]
    }
}
```

These JSON schemas are collected into a list:

```python
tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]
```

This list is passed to the model in the chat call:

```python
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools
)
```

---

## 🧰 The Available Tools

### 1. `record_user_details(email, name, notes)`
Used when a user shares contact details or interest.  
It triggers a **Pushover notification** and returns confirmation.

```python
def record_user_details(email, name="Name not provided", notes="Not provided"):
    push(f"Recording interest from {name} with email {email} and notes: {notes}")
    return {"recorded": "ok"}
```

### 2. `record_unknown_question(question)`
Used when the AI can’t answer a question.  
It logs the question via **Pushover** and returns confirmation.

```python
def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}
```

---

## 🧩 Handling Tool Calls

When the assistant decides a tool should be called, the OpenAI response includes a **`tool_calls`** section.  

The class method `handle_tool_call` manages this:

```python
def handle_tool_call(self, tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({
            "role": "tool",
            "content": json.dumps(result),
            "tool_call_id": tool_call.id
        })
    return results
```

Essentially:
1. The AI says “I want to call `record_user_details` with `{email: ..., name: ...}`.”
2. The handler looks up the function by name.
3. Executes it with the provided arguments.
4. Appends the tool’s output back into the chat context.
5. The model continues the conversation, now aware of the tool’s result.

---

## 💬 Chat Loop Logic

```python
while not done:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools
    )
    if response.choices[0].finish_reason == "tool_calls":
        tool_calls = response.choices[0].message.tool_calls
        results = self.handle_tool_call(tool_calls)
        messages.append(response.choices[0].message)
        messages.extend(results)
    else:
        done = True
```

This loop continues until the assistant is finished responding — even if it had to call multiple tools in sequence.

---

## 🧠 System Prompt (Persona Setup)

The assistant acts as **Ypatios Chaniotakos**, using their résumé and summary files for grounding:

```
You are acting as Ypatios Chaniotakos...
If you don't know the answer, use the record_unknown_question tool.
If the user provides contact info, use record_user_details.
```

This ensures that tool usage feels natural — like a real professional assistant managing contact inquiries.

---

## 🖥️ Running the Assistant

1. Install dependencies:
   ```bash
   pip install openai gradio python-dotenv pypdf requests
   ```

2. Set up your `.env` file (see Pushover setup above).

3. Run the assistant:
   ```bash
   python me_with_tools.py
   ```

4. Open the Gradio web UI in your browser (it will print a localhost URL).

5. Chat naturally — try saying things like:
   - “Here’s my email, please contact me.”
   - “I have a question about quantum computing.”

   You’ll get push notifications when tools trigger!

---

## 📲 Example Push Notifications

```
Pushing notification: Recording interest from John Doe with email john@example.com and notes: Interested in collaboration.
Pushing notification: Recording What is your favorite food? asked that I couldn't answer
```

---

## ✅ Summary of Concepts

| Concept | Description |
|----------|--------------|
| **Tool definition** | Describes what functions the model can call (in JSON schema). |
| **Tool call** | The model’s structured request to execute a function. |
| **Handler** | Code that executes the function, returns output to the model. |
| **Pushover integration** | Sends real-time mobile alerts when tools are triggered. |

---

## 🧭 Next Steps

- Add more tools (e.g., `schedule_meeting`, `fetch_portfolio_link`).
- Extend `record_user_details` to save data to a database.
- Improve push notification messages with timestamps or structured summaries.
- Combine with an **evaluator agent** for self-quality checks.

---

**Author:** Ypatios Chaniotakos  
**Date:** October 2025  
**Project:** AI Assistant with Function Tools & Pushover Notifications
