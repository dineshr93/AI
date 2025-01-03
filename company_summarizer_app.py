# imports

import os
import requests
from bs4 import BeautifulSoup
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai
import anthropic
import ollama
import gradio as gr # oh yeah!

# Load environment variables in a file called .env
# Print the key prefixes to help with any debugging

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY','your_optional_default_key_here')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY','your_optional_default_key_here')
google_api_key = os.getenv('GOOGLE_API_KEY','your_optional_default_key_here')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
if anthropic_api_key:
    print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
else:
    print("Anthropic API Key not set")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:8]}")
else:
    print("Google API Key not set")

# Connect to OpenAI, Anthropic and Google; comment out the Claude or Google lines if you're not using them

# openai = OpenAI()

# claude = anthropic.Anthropic()

# google.generativeai.configure()

# A class to represent a Webpage
class Website:
    url: str
    title: str
    text: str

    def __init__(self, url):
        self.url = url
        response = requests.get(url)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"

system_message = "You are an assistant that analyzes the contents of a company website landing page \
and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown."

def stream_ollama(prompt):
    # Constants
    # OLLAMA_API = "http://localhost:11434/api/chat"
    # HEADERS = {"Content-Type": "application/json"}
    # MODEL = "llama3.2"
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    # response = requests.post(OLLAMA_API, json=messages, headers=HEADERS)
    # result = response.json()['message']['content']
    # return result
    stream = ollama.chat(
        model="llama3.2", 
        messages=messages,
        stream=True
    )
    result = ""
    for chunk in stream:
        result += chunk['message']['content'] or ""
        yield result

    # For stream = False 
    # result = response['message']['content']
    # return result

def stream_gpt(prompt):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
      ]
    stream = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        stream=True
    )
    result = ""
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result

def stream_claude(prompt):
    result = claude.messages.stream(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.7,
        system=system_message,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    response = ""
    with result as stream:
        for text in stream.text_stream:
            response += text or ""
            yield response


def stream_brochure(company_name, url, model):
    prompt = f"Please generate a company brochure for {company_name}. Here is their landing page:\n"
    prompt += Website(url).get_contents()
    if model=="GPT":
        result = stream_gpt(prompt)
    elif model=="Claude":
        result = stream_claude(prompt)
    elif model=="Ollama":
        result = stream_ollama(prompt)
    else:
        raise ValueError("Unknown model")
    yield from result

view = gr.Interface(
fn=stream_brochure,
inputs=[
    gr.Textbox(label="Company name:"),
    gr.Textbox(label="Landing page URL including http:// or https://"),
    gr.Dropdown(["Ollama","GPT", "Claude"], label="Select model")],
outputs=[gr.Markdown(label="Brochure:")],
flagging_mode="never"
)
view.launch()