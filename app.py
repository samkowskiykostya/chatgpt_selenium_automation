import asyncio
import json
import re
import time
from typing import List

import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from handler.chatgpt_selenium_automation import ChatGPTAutomation

app = FastAPI()

CHROME_DRIVER_PATH = "/home/max/Install/chromedrivers/chromedriver-114.0.5735.90"
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


@app.post("/chat/completions")
async def create_chat_stream_completion(request: Request):
    body = await request.json()
    if "messages" not in body:
        raise HTTPException(status_code=400, detail="Missing 'messages' key in request body.")
    if not isinstance(body["messages"], list):
        raise HTTPException(status_code=400, detail="'messages' must be a list.")
    CHATGPT.send_prompt_to_chatgpt(body['messages'][-1]['content'][0]['text'])
    prompt = CHATGPT.return_last_response()
    # prompt = "Hello! I am happy to help you whatever you are interested in"
    return StreamingResponse(chat_stream_generator(prompt), media_type="text/event-stream")


def chat_stream_generator(text: str):
    tokens = re.findall(r"\S+|\s+", text)  # Split while keeping spaces and other symbols
    for i, token in enumerate(tokens):
        event_data = {
            "id": f"chatcmpl-9TeIgRFGsZamIdzCJt2jEBtLFmyMs{i}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "gpt-4o-2024-05-13",
            "system_fingerprint": "fp_43dfabdef1",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": token},
                    "logprobs": None,
                    "finish_reason": None,
                }
            ],
            "usage": None,
        }
        yield f"data: {json.dumps(event_data)}\n\n"


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
