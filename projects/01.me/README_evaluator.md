# Self‑Evaluating AI Chat Assistant (Agentic Demo)

This project is an **agentic AI** notebook that shows how to make a chat assistant **generate → evaluate → revise** its own answers. It does this by pairing a *writer* model with a *judge* model and using **typed structured outputs** (via Pydantic) to control the feedback loop.

---

## ✨ What you’ll see

- **Generator** (writer): produces a first reply using `gpt-4o-mini`.
- **Evaluator** (judge): returns a strict, typed verdict:
  ```py
  class Evaluation(BaseModel):
      is_acceptable: bool
      feedback: str
  ```
  Thanks to the OpenAI SDK’s `chat.completions.parse(...)`, the model’s output is parsed **directly into this Pydantic object** — no manual JSON parsing.
- **Rerun** (fixer): if the evaluator says ❌, we **automatically re-prompt** the generator with the feedback and return the corrected answer.

A tiny **Gradio** UI wires everything into a runnable chat.

---

## 🧠 Why the “patent → Pig Latin” trick?

The notebook includes a deliberate test hook:

```py
if "patent" in message:
    system = system_prompt + """

Everything in your reply needs to be in pig latin - 
          it is mandatory that you respond only and entirely in pig latin""" 
```

- When the user’s message contains **“patent”**, we *force* a low‑quality reply (Pig Latin).
- The **evaluator** should flag that as unacceptable and provide actionable feedback.
- The **rerun** uses that feedback to produce a clean, professional answer.

This gives you a reliable way to *see the evaluation loop in action* during demos, instead of waiting for a natural failure.

> Don’t want the demo behavior? Delete the `if "patent"` block — everything else still works.

---

## 🧩 How it works (flow)

1. **Build system context**  
   The assistant is instructed to act as a specific persona (from a résumé/LinkedIn summary you load in the notebook). This goes into the system prompt so replies are on‑brand and grounded.

2. **Generate a first draft**
   ```py
   response = openai.chat.completions.create(
       model="gpt-4o-mini",
       messages=[{"role":"system","content":system_prompt}, *history, {"role":"user","content":message}],
   )
   reply = response.choices[0].message.content
   ```

3. **Evaluate the draft (structured)**
   ```py
   from pydantic import BaseModel

   class Evaluation(BaseModel):
       is_acceptable: bool
       feedback: str

   evaluation = client.chat.completions.parse(
       model="gpt-4o-mini",
       messages=[
         {"role":"system","content":evaluator_system_prompt},
         {"role":"user","content":evaluator_user_prompt(reply, message, history)}
       ],
       response_format=Evaluation,
       temperature=0.1,
   ).choices[0].message.parsed
   ```

4. **Gate + Rerun if needed**
   ```py
   if evaluation.is_acceptable:
       return reply
   else:
       improved = rerun(reply, message, history, evaluation.feedback)
       return improved
   ```

5. **UI**  
   A small **Gradio** `ChatInterface` function calls `chat(...)` and streams replies.

---

## 🧱 Key files (as used in the notebook)

- `me_with_evaluation.ipynb` — the full demo notebook (chat, evaluator, rerun, UI).
- `me/summary.txt` — short bio/persona summary used for grounding.
- `me/bio.pdf` — profile text loaded to enrich the system prompt.

> If you’re adapting this to your own profile, replace the files in `me/` and keep the same loading logic.

---

## 🛠️ Rerun strategy (prompting pattern)

`rerun(...)` augments the generator’s system prompt with:
- The **failed reply** (verbatim)
- The **evaluator’s feedback** (verbatim)
- A short instruction: *“Revise the reply to satisfy the feedback exactly; don’t repeat the same mistakes; keep persona and constraints.”*

This “critique → revise” loop is the backbone of many **agentic** systems.

---

## 🧪 Quick demo steps

1. Launch the notebook.
2. Ask a normal question — expect a solid reply.
3. Ask something with the word **“patent”** — assistant will try to talk in pig Latin.
4. See the evaluator flag it as not acceptable answer providing a feedback as well and rerun the process.

---

