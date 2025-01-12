# https://github.com/ed-donner/llm_engineering/blob/main/week4/day4.ipynb
# imports

import os
import io
import sys
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai
import anthropic
from IPython.display import Markdown, display, update_display
import gradio as gr
import subprocess
from huggingface_hub import login, InferenceClient
from transformers import AutoTokenizer
import platform

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

code_qwen = "Qwen/CodeQwen1.5-7B-Chat"
code_gemma = "google/codegemma-7b-it"
CODE_QWEN_URL = "https://dfsfas.us-east-1.aws.endpoints.huggingface.cloud"
CODE_GEMMA_URL = "https://asdfsdchmgnqg.us-east-1.aws.endpoints.huggingface.cloud"

system_message = "You are an assistant that reimplements Python code in high performance C++ for an M1 Mac. "
system_message += "Respond only with C++ code; use comments sparingly and do not provide any explanation other than occasional comments. "
system_message += "The C++ response needs to produce an identical output in the fastest possible time. Keep implementations of random number generators identical so that results match exactly."
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

tokenizer = AutoTokenizer.from_pretrained(code_qwen)
messages = messages_for(pi)
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

client = InferenceClient(CODE_QWEN_URL, token=hf_token)
stream = client.text_generation(text, stream=True, details=True, max_new_tokens=3000)
for r in stream:
    print(r.token.text, end = "")

def stream_code_qwen(python):
    tokenizer = AutoTokenizer.from_pretrained(code_qwen)
    messages = messages_for(python)
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    client = InferenceClient(CODE_QWEN_URL, token=hf_token)
    stream = client.text_generation(text, stream=True, details=True, max_new_tokens=3000)
    result = ""
    for r in stream:
        result += r.token.text
        yield result

def stream_gpt(python):    
    stream = openai.chat.completions.create(model=OPENAI_MODEL, messages=messages_for(python), stream=True)
    reply = ""
    for chunk in stream:
        fragment = chunk.choices[0].delta.content or ""
        reply += fragment
        yield reply.replace('```cpp\n','').replace('```','')
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

def optimize(python, model):
    if model=="GPT":
        result = stream_gpt(python)
    elif model=="Claude":
        result = stream_claude(python)
    elif model=="CodeQwen":
        result = stream_code_qwen(python)
    else:
        raise ValueError("Unknown model")
    for stream_so_far in result:
        yield stream_so_far
# import platform

VISUAL_STUDIO_2022_TOOLS = "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\Common7\Tools\\VsDevCmd.bat"
VISUAL_STUDIO_2019_TOOLS = "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\BuildTools\\Common7\\Tools\\VsDevCmd.bat"

simple_cpp = """
#include <iostream>

int main() {
    std::cout << "Hello";
    return 0;
}
"""

def run_cmd(command_to_run):
    try:
        run_result = subprocess.run(command_to_run, check=True, text=True, capture_output=True)
        return run_result.stdout if run_result.stdout else "SUCCESS"
    except:
        return ""

def c_compiler_cmd(filename_base):
    my_platform = platform.system()
    my_compiler = []

    try:
        with open("simple.cpp", "w") as f:
            f.write(simple_cpp)
            
        if my_platform == "Windows":
            if os.path.isfile(VISUAL_STUDIO_2022_TOOLS):
                if os.path.isfile("./simple.exe"):
                    os.remove("./simple.exe")
                compile_cmd = ["cmd", "/c", VISUAL_STUDIO_2022_TOOLS, "&", "cl", "simple.cpp"]
                if run_cmd(compile_cmd):
                    if run_cmd(["./simple.exe"]) == "Hello":
                        my_compiler = ["Windows", "Visual Studio 2022", ["cmd", "/c", VISUAL_STUDIO_2022_TOOLS, "&", "cl", f"{filename_base}.cpp"]]
        
            if not my_compiler:
                if os.path.isfile(VISUAL_STUDIO_2019_TOOLS):
                    if os.path.isfile("./simple.exe"):
                        os.remove("./simple.exe")
                    compile_cmd = ["cmd", "/c", VISUAL_STUDIO_2019_TOOLS, "&", "cl", "simple.cpp"]
                    if run_cmd(compile_cmd):
                        if run_cmd(["./simple.exe"]) == "Hello":
                            my_compiler = ["Windows", "Visual Studio 2019", ["cmd", "/c", VISUAL_STUDIO_2019_TOOLS, "&", "cl", f"{filename_base}.cpp"]]
    
            if not my_compiler:
                my_compiler=[my_platform, "Unavailable", []]
                
        elif my_platform == "Linux":
            if os.path.isfile("./simple"):
                os.remove("./simple")
            compile_cmd = ["g++", "simple.cpp", "-o", "simple"]
            if run_cmd(compile_cmd):
                if run_cmd(["./simple"]) == "Hello":
                    my_compiler = ["Linux", "GCC (g++)", ["g++", f"{filename_base}.cpp", "-o", f"{filename_base}" ]]
    
            if not my_compiler:
                if os.path.isfile("./simple"):
                    os.remove("./simple")
                compile_cmd = ["clang++", "simple.cpp", "-o", "simple"]
                if run_cmd(compile_cmd):
                    if run_cmd(["./simple"]) == "Hello":
                        my_compiler = ["Linux", "Clang++", ["clang++", f"{filename_base}.cpp", "-o", f"{filename_base}"]]
        
            if not my_compiler:
                my_compiler=[my_platform, "Unavailable", []]
    
        elif my_platform == "Darwin":
            if os.path.isfile("./simple"):
                os.remove("./simple")
            compile_cmd = ["clang++", "-Ofast", "-std=c++17", "-march=armv8.5-a", "-mtune=apple-m1", "-mcpu=apple-m1", "-o", "simple", "simple.cpp"]
            if run_cmd(compile_cmd):
                if run_cmd(["./simple"]) == "Hello":
                    my_compiler = ["Macintosh", "Clang++", ["clang++", "-Ofast", "-std=c++17", "-march=armv8.5-a", "-mtune=apple-m1", "-mcpu=apple-m1", "-o", f"{filename_base}", f"{filename_base}.cpp"]]
    
            if not my_compiler:
                my_compiler=[my_platform, "Unavailable", []]
    except:
        my_compiler=[my_platform, "Unavailable", []]
        
    if my_compiler:
        return my_compiler
    else:
        return ["Unknown", "Unavailable", []]

compiler_cmd = c_compiler_cmd("optimized")
pi = """
import time

def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

start_time = time.time()
result = calculate(100_000_000, 4, 1) * 4
end_time = time.time()

print(f"Result: {result:.12f}")
print(f"Execution Time: {(end_time - start_time):.6f} seconds")
"""

python_hard = """
import time

def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

start_time = time.time()
result = calculate(100_000_000, 4, 1) * 4
end_time = time.time()

print(f"Result: {result:.12f}")
print(f"Execution Time: {(end_time - start_time):.6f} seconds")
"""
def select_sample_program(sample_program):
    if sample_program=="pi":
        return pi
    elif sample_program=="python_hard":
        return python_hard
    else:
        return "Type your Python program here"
def execute_python(code):
    try:
        output = io.StringIO()
        sys.stdout = output
        exec(code)
    finally:
        sys.stdout = sys.__stdout__
    return output.getvalue()

# write to a file called optimized.cpp

def write_output(cpp):
    code = cpp.replace("```cpp","").replace("```","")
    with open("optimized.cpp", "w") as f:
        f.write(code)
        
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
css  = """
.python {background-color: #306998;}
.cpp {background-color: #050;}
"""
with gr.Blocks(css=css) as ui:
    gr.Markdown("## Convert code from Python to C++")
    with gr.Row():
        python = gr.Textbox(label="Python code:", value=python_hard, lines=10)
        cpp = gr.Textbox(label="C++ code:", lines=10)
    with gr.Row():
        with gr.Column():
            sample_program = gr.Radio(["pi", "python_hard"], label="Sample program", value="python_hard")
            model = gr.Dropdown(["GPT", "Claude", "CodeQwen"], label="Select model", value="GPT")
        with gr.Column():
            architecture = gr.Radio([compiler_cmd[0]], label="Architecture", interactive=False, value=compiler_cmd[0])
            compiler = gr.Radio([compiler_cmd[1]], label="Compiler", interactive=False, value=compiler_cmd[1])
    with gr.Row():
        convert = gr.Button("Convert code")
    with gr.Row():
        python_run = gr.Button("Run Python")
        if not compiler_cmd[1] == "Unavailable":
            cpp_run = gr.Button("Run C++")
        else:
            cpp_run = gr.Button("No compiler to run C++", interactive=False)
    with gr.Row():
        python_out = gr.TextArea(label="Python result:", elem_classes=["python"])
        cpp_out = gr.TextArea(label="C++ result:", elem_classes=["cpp"])

    sample_program.change(select_sample_program, inputs=[sample_program], outputs=[python])
    convert.click(optimize, inputs=[python, model], outputs=[cpp])
    python_run.click(execute_python, inputs=[python], outputs=[python_out])
    cpp_run.click(execute_cpp_on_windows, inputs=[cpp], outputs=[cpp_out])

ui.launch(inbrowser=True)