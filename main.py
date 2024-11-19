import uvicorn
from llm.llm import VirtualNurseLLM
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

# model: typhoon-v1.5x-70b-instruct
nurse_llm = VirtualNurseLLM(
    base_url="https://api.opentyphoon.ai/v1",
    model="typhoon-v1.5x-70b-instruct",
    api_key=os.getenv("TYPHOON_CHAT_KEY")
)

# model: OpenThaiGPT
# nurse_llm = VirtualNurseLLM(
#     base_url="https://api.aieat.or.th/v1",
#     model=".",
#     api_key="dummy"
# )

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    user_input: str
    model_name: str = "typhoon-v1.5x-70b-instruct"

class NurseResponse(BaseModel):
    nurse_response: str

class EHRData(BaseModel):
    ehr_data: dict
    current_context: str
    current_prompt: str
    current_prompt_ehr: str
    current_patient_response: str
    current_question: str

class ChatHistory(BaseModel):
    chat_history: list
    
@app.get("/", response_class=HTMLResponse)
def read_index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MALI_NURSE API/title>
    </head>
    <body>
        <h1>Welcome to MALI_NURSE API</h1>
        <p>This is the index page. Use the link below to access the API docs:</p>
        <a href="/docs">Go to Swagger Docs UI</a>
    </body>
    </html>
    """

@app.get("/history")
def get_chat_history():
    return ChatHistory(chat_history = nurse_llm.chat_history)

@app.get("/details")
def get_ehr_data():
    return EHRData(
        ehr_data=nurse_llm.ehr_data,
        current_context=nurse_llm.current_context,
        current_prompt=nurse_llm.current_prompt,
        current_prompt_ehr=nurse_llm.current_prompt_ehr,
        current_patient_response=nurse_llm.current_patient_response,
        current_question=nurse_llm.current_question
    )

def toggle_debug():
    nurse_llm.debug = not nurse_llm.debug
    return {"debug_mode": "on" if nurse_llm.debug else "off"}


@app.post("/reset")
def data_reset():
    nurse_llm.reset()
    print("Chat history and EHR data have been reset.")

@app.post("/nurse_response")
def nurse_response(user_input: UserInput):
    """
    Models: "typhoon-v1.5x-70b-instruct (default)", "openthaigpt"
    """
    if user_input.model_name == "typhoon-v1.5x-70b-instruct":
        nurse_llm.model = "typhoon-v1.5x-70b-instruct"
    elif user_input.model_name == "openthaigpt":
        nurse_llm.model = "openthaigpt"
    else:
        return {"error": "Invalid model name"}
    response = nurse_llm.invoke(user_input.user_input)
    return NurseResponse(nurse_response = response)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)