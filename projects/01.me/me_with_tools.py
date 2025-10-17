from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import json
from pypdf import PdfReader
import gradio as gr
from typing import Any, cast

load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = os.getenv("PUSHOVER_URL") or ""

def push(message):
    print(f"Pushing notification: {message}")
    payload = {
        "token": pushover_token,
        "user": pushover_user,
        "message": message
    }
    requests.post(pushover_url, data=payload)


# ---------------
# function tools
# ---------------

def record_user_details(email, name="Name not provided", notes="Not provided"):
    push(f"Recording interest from {name} with email {email} and notes: {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}

# -----------
# json tools
# -----------

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch ans provided an email adress",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email adress of this user"
            },
            "name": {
                "type": "string",
                "description": "The name of this user"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information that is worth recording"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered or you didn't know the answer to",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

# -------------------------
# create the list of tools
# -------------------------

tools = [{"type": "function", "function": record_user_details_json},
         {"type": "function", "function": record_unknown_question_json}]

# ----------
# create me 
# ----------

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Ypatios Chaniotakos"

        base_dir = os.path.dirname(__file__)
        pdf_path = os.path.join(base_dir, "data", "chaniotakos.pdf")
        reader = PdfReader(pdf_path)

        self.bio = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.bio += text

        base_dir = os.path.dirname(__file__)
        summary_path = os.path.join(base_dir, "data", "summary.txt")
        with open(summary_path, "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and bio profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## bio Profile:\n{self.bio}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        response = None
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=cast(Any, tools))
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        if response is None:
            return ""
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    


