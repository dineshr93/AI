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

openai = OpenAI()
claude = anthropic.Anthropic()
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

def execute_python(code):
    try:
        output = io.StringIO()
        sys.stdout = output
        exec(code)
    finally:
        sys.stdout = sys.__stdout__
    return output.getvalue()

# You'll need to change the code in the try block to compile the C++ code for your platform
# I pasted this into Claude's chat UI with a request for it to give me a version for an Intel PC,
# and it responded with something that looks perfect - you can try a similar approach for your platform.

# M1 Mac version to compile and execute optimized C++ code:

def execute_cpp(code):
        write_output(code)
        try:
            compile_cmd = ["clang++", "-Ofast", "-std=c++17", "-march=armv8.5-a", "-mtune=apple-m1", "-mcpu=apple-m1", "-o", "optimized", "optimized.cpp"]
            compile_result = subprocess.run(compile_cmd, check=True, text=True, capture_output=True)
            run_cmd = ["./optimized"]
            run_result = subprocess.run(run_cmd, check=True, text=True, capture_output=True)
            return run_result.stdout
        except subprocess.CalledProcessError as e:
            return f"An error occurred:\n{e.stderr}"
        
def execute_cpp_on_windows(code):
    # Write the C++ code to a file
    write_output(code)
    
    try:
        # Compile the C++ file
        compile_cmd = ["g++", "-Ofast", "-std=c++17", "-o", "optimized.exe", "optimized.cpp"]
        compile_result = subprocess.run(compile_cmd, check=True, text=True, capture_output=True)
        
        # Run the compiled executable
        run_cmd = ["optimized.exe"]
        run_result = subprocess.run(run_cmd, check=True, text=True, capture_output=True)
        
        # Return the output of the executable
        return run_result.stdout
    
    except subprocess.CalledProcessError as e:
        return f"An error occurred:\n{e.stderr}"

css = """
.python {background-color: #306998;}
.cpp {background-color: #050;}
"""


with gr.Blocks(css=css) as ui:
    gr.Markdown("## Convert code from Python to C++")
    with gr.Row():
        # python = gr.Textbox(label="Python code:", value=python_hard, lines=10)
        python = gr.Textbox(label="Python code:", lines=10)
        cpp = gr.Textbox(label="C++ code:", lines=10)
    with gr.Row():
        model = gr.Dropdown(["CODELAMMA","GPT", "Claude"], label="Select model", value="CODELAMMA")
    with gr.Row():
        convert = gr.Button("Convert code")
    with gr.Row():
        python_run = gr.Button("Run Python")
        cpp_run = gr.Button("Run C++")
    with gr.Row():
        python_out = gr.TextArea(label="Python result:", elem_classes=["python"])
        cpp_out = gr.TextArea(label="C++ result:", elem_classes=["cpp"])

    convert.click(optimize, inputs=[python, model], outputs=[cpp])
    python_run.click(execute_python, inputs=[python], outputs=[python_out])
    cpp_run.click(execute_cpp_on_windows, inputs=[cpp], outputs=[cpp_out])

ui.launch(inbrowser=True)