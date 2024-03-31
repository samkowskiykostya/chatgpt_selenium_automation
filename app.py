import uvicorn
import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from handler.chatgpt_selenium_automation import ChatGPTAutomation
from bs4 import BeautifulSoup


app = FastAPI()

CHROME_DRIVER_PATH = "/home/max/Install/chromedriver"
CHROME_PATH = "/home/max/w/_github/chrome/linux-114.0.5735.133/chrome-linux64/chrome"
CHATGPT = None


class Message(BaseModel):
    # role: str
    content: str


class CompletionRequest(BaseModel):
    # model: str
    messages: List[Message]
    # temperature: float


@app.post("/api/chat/completions")
async def create_chat_completion(request: CompletionRequest):
    prompt = "\n".join([a.content for a in request.messages])
    CHATGPT.send_prompt_to_chatgpt(prompt)

    response = fixup_response(CHATGPT.return_last_response())
    print(response)
    return json.dumps({"role": "assistant", "content": response})


@app.get("/latest")
async def create_chat_completion():
    response = fixup_response(CHATGPT.return_last_response())
    print(response)
    return json.dumps({"role": "assistant", "content": response})


def fixup_response(input_text):
    lines = input_text.split("\n")
    processed_lines = []
    copy_code_found = False
    for i, line in enumerate(lines):
        # If the current line is "Copy code", modify the previous line if it exists
        if line == "Copy code":
            if processed_lines:  # Check if there's a previous line to modify
                # Modify the previous line by adding "```" prefix
                processed_lines[-1] = f"```{processed_lines[-1]}"
            copy_code_found = True  # Mark that "Copy code" was found
        elif copy_code_found and line.startswith(">>>>>>> updated"):
            # If "Copy code" was found and this is the updated marker line, append "```" after it
            processed_lines.append(line)  # Add the current line first
            processed_lines.append("```")  # Then add the "```" to close the code block
            copy_code_found = False  # Reset the flag
        else:
            # If "Copy code" wasn't just found, add the line as usual
            processed_lines.append(line)

    # Join the processed lines back into a single string and return it
    return "\n".join(processed_lines)


if __name__ == "__main__":
    CHATGPT = ChatGPTAutomation(CHROME_PATH, CHROME_DRIVER_PATH)
    uvicorn.run(app, host="0.0.0.0", port=8100)
