"""The whole idea of an agent, with no framework.

Loop: ask model -> model asks for a tool -> we run it -> give result back -> repeat.
Run:  python agent.py "What is 23 * 47, and what time is it?"
"""
import sys
from datetime import datetime
import os

from google import genai
from google.genai import types

MODEL = os.getenv("MODEL", "gemini-2.5-flash")
MAX_STEPS = 5  # stop condition: never loop forever


# 1. TOOLS: plain Python functions
def calculator(expression: str) -> str:
    return str(eval(expression, {"__builtins__": {}}))  # toy only, never eval untrusted input


def current_time() -> str:
    return datetime.now().strftime("%H:%M")


TOOLS = {"calculator": calculator, "current_time": current_time}

# 2. TOOL DESCRIPTIONS: this is all the model "sees" of your tools
tool_spec = types.Tool(function_declarations=[
    {"name": "calculator", "description": "Evaluate a math expression like '2*(3+4)'.",
     "parameters": {"type": "object", "properties": {"expression": {"type": "string"}},
                    "required": ["expression"]}},
    {"name": "current_time", "description": "Get the current local time.",
     "parameters": {"type": "object", "properties": {}}},
])
config = types.GenerateContentConfig(tools=[tool_spec])


def run(question: str) -> str:
    client = genai.Client()  # reads GEMINI_API_KEY from env
    history = [types.Content(role="user", parts=[types.Part(text=question)])]

    # 3. THE LOOP
    for step in range(1, MAX_STEPS + 1):
        response = client.models.generate_content(model=MODEL, contents=history, config=config)
        history.append(response.candidates[0].content)  # remember what the model said

        if not response.function_calls:  # no tool requested -> model is done
            return response.text

        for call in response.function_calls:  # model wants tools -> run them
            result = TOOLS[call.name](**(call.args or {}))
            print(f"  step {step}: {call.name}({dict(call.args or {})}) -> {result}")
            history.append(types.Content(role="user", parts=[
                types.Part.from_function_response(name=call.name, response={"result": result})
            ]))

    return "Stopped: hit MAX_STEPS."


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is 23 * 47, and what time is it?"
    print("Answer:", run(q))
