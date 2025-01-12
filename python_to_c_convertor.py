# imports

import os
import io
import sys
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai
import anthropic
from IPython.display import Markdown, display, update_display
import gradio as gr
import subprocess
import ollama

# environment

load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'your-key-if-not-using-env')

# initialize
# NOTE - option to use ultra-low cost models by uncommenting last 2 lines

# openai = OpenAI()
# claude = anthropic.Anthropic()
OPENAI_MODEL = "gpt-4o"
CLAUDE_MODEL = "claude-3-5-sonnet-20240620"
CODELLAMA_MODEL = "codellama"

# Want to keep costs ultra-low? Uncomment these lines:
# OPENAI_MODEL = "gpt-4o-mini"
# CLAUDE_MODEL = "claude-3-haiku-20240307"

system_message = "You are an assistant that reimplements Python code in high performance C++ for an M1 Mac. "
system_message += "Respond only with C++ code; use comments sparingly and do not provide any explanation other than occasional comments. "
system_message += "The C++ response needs to produce an identical output in the fastest possible time."

def user_prompt_for(python):
    user_prompt = "Rewrite this Python code in C++ with the fastest possible implementation that produces identical output in the least time. "
    user_prompt += "Respond only with C++ code; do not explain your work other than a few comments. "
    user_prompt += "Pay attention to number types to ensure no int overflows. Remember to #include all necessary C++ packages such as iomanip.\n\n"
    user_prompt += python
    return user_prompt

def messages_for(python):
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt_for(python)}
    ]

# write to a file called optimized.cpp

def write_output(cpp):
    code = cpp.replace("```cpp","").replace("```","")
    with open("optimized.cpp", "w") as f:
        f.write(code)

# def optimize_gpt(python):    
#     stream = openai.chat.completions.create(model=OPENAI_MODEL, messages=messages_for(python), stream=True)
#     reply = ""
#     for chunk in stream:
#         fragment = chunk.choices[0].delta.content or ""
#         reply += fragment
#         print(fragment, end='', flush=True)
#     write_output(reply)

def stream_gpt(python):    
    stream = openai.chat.completions.create(model=OPENAI_MODEL, messages=messages_for(python), stream=True)
    reply = ""
    for chunk in stream:
        fragment = chunk.choices[0].delta.content or ""
        reply += fragment
        yield reply.replace('```cpp\n','').replace('```','')

# def optimize_claude(python):
#     result = claude.messages.stream(
#         model=CLAUDE_MODEL,
#         max_tokens=2000,
#         system=system_message,
#         messages=[{"role": "user", "content": user_prompt_for(python)}],
#     )
#     reply = ""
#     with result as stream:
#         for text in stream.text_stream:
#             reply += text
#             print(text, end="", flush=True)
#     write_output(reply)

def stream_claude(python):
    result = claude.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=system_message,
        messages=[{"role": "user", "content": user_prompt_for(python)}],
    )
    reply = ""
    with result as stream:
        for text in stream.text_stream:
            reply += text
            yield reply.replace('```cpp\n','').replace('```','')

def stream_ollama(python):
    # Constants
    # OLLAMA_API = "http://localhost:11434/api/chat"
    # HEADERS = {"Content-Type": "application/json"}
    # MODEL = "llama3.2"
    # messages = [
    #     {"role": "system", "content": system_message},
    #     {"role": "user", "content": python}
    # ]
    # response = requests.post(OLLAMA_API, json=messages, headers=HEADERS)
    # result = response.json()['message']['content']
    # return result
    stream = ollama.chat(
        model=CODELLAMA_MODEL, 
        messages=messages_for(python),
        stream=True
    )
    result = ""
    for chunk in stream:
        result += chunk['message']['content'] or ""
        yield result

def optimize(python, model):
    if model=="CODELAMMA":
        result = stream_ollama(python)
    elif model=="GPT":
        result = stream_gpt(python)
    elif model=="Claude":
        result = stream_claude(python)
    else:
        raise ValueError("Unknown model")
    for stream_so_far in result:
        yield stream_so_far

with gr.Blocks() as ui:
    with gr.Row():
        python = gr.Textbox(label="Python code:", lines=10)
        cpp = gr.Textbox(label="C++ code:", lines=10)
    with gr.Row():
        model = gr.Dropdown(["CODELAMMA","GPT", "Claude"], label="Select model", value="CODELAMMA")
        convert = gr.Button("Convert code")

    convert.click(optimize, inputs=[python, model], outputs=[cpp])

ui.launch(inbrowser=True)