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

    response = CHATGPT.return_last_response()
    print(response)
    return json.dumps({"role": "assistant", "content": response})

@app.get("/latest")
async def create_chat_completion():
    response = CHATGPT.return_last_response()
    print(response)
    return json.dumps({"role": "assistant", "content": response})



if __name__ == "__main__":
    CHATGPT = ChatGPTAutomation(CHROME_PATH, CHROME_DRIVER_PATH)
    uvicorn.run(app, host="0.0.0.0", port=8100)
