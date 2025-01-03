# imports

import requests
from bs4 import BeautifulSoup
from IPython.display import Markdown, display
from rich.console import Console
from rich.markdown import Markdown
import gradio as gr
console = Console()

# Constants

OLLAMA_API = "http://localhost:11434/api/chat"
OLLAMA_API_G = "http://localhost:11434/api/generate"
HEADERS = {"Content-Type": "application/json"}
MODEL = "llama3.2"
# MODELC = "codellama"
# MODELG = "gemma2:27b"

# Create a messages list using the same format that we used for OpenAI



# img = open("images.jpg", 'r').read()
# messages = [
#     {"role": "system", 
#      "content": "You are a funny assistant. generate the output text in markdown"},
#     {"role": "user", 
#      "content": f"what is in this image:\n\n" + img}
# ]

# messages = [
#     {"role": "system", "content": "You are an expert at counting alphabets"},
#     {"role": "user", "content": "how many letter 'a' is present in this sentence 'You are a funny assistant'"}
# ]


# payload = {
#         "model": MODEL,
#         "messages": messages,
#         "stream": False
#     }

# Let's just make sure the model is loaded -> ollama pull llama3.2
def code_explainer(file):
    code = open(file, 'r').read()
    messages = [
        {"role": "system", 
        "content": "You are an software assistant that analyzes the source code section by section according to logical groupings. generate the output text in colorful markdowns"},
        {"role": "user", 
        "content": f"Explain this code:\n\n" + code}
    ]
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }
    response = requests.post(OLLAMA_API, json=payload,headers=HEADERS)
# markdown_text = response.content
# print(markdown_text)
    markdown_text = response.json()['message']['content']
    return markdown_text


# md = Markdown(markdown_text)
# console.print(md)

# method1
# view = gr.Interface(
#     fn=code_explainer,
#     inputs=gr.File(label="Upload a Source File"),
#     outputs=[gr.Markdown(label="Response:")],
#     flagging_mode="never"
# )
# view.launch()

# method2
with gr.Blocks() as view:
    input_text = gr.File(label="Upload a Source File")
    # input_text = gr.Textbox(label="Enter some text")
    output_text = gr.Markdown(label="Response:")
    # download_file = gr.File(label="Download your file")
    
    btn = gr.Button("Explain the Code")
    # btn = gr.Button("Generate File")
    btn.click(
        fn=code_explainer, 
        inputs=input_text, 
        outputs=output_text
    )

view.launch()