from litellm import completion

MODEL="llama3.2:latest"
MODEL="codellama:latest"
response = completion(
            model=f"ollama/{MODEL}",
            messages = [{ "content": "Please write a bash script hello.sh that prints 'hello world!'","role": "user"}],
            api_base="http://localhost:11434"
)
print(response.choices[0].message.content)