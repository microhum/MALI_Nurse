from typing import Optional
import uvicorn
from llm.basemodel import EHRModel
from llm.llm import VirtualNurseLLM
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from llm.models import model_list, get_model
import time

initial_model = "typhoon-v1.5x-70b-instruct"
nurse_llm = VirtualNurseLLM(
    # base_url=model_list[initial_model]["base_url"],
    model_name=model_list[initial_model]["model_name"],
    # api_key=model_list[initial_model]["api_key"]
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
    ehr_data: Optional[EHRModel]
    current_context: Optional[str]
    current_prompt: Optional[str]
    current_prompt_ehr: Optional[str]
    current_patient_response: Optional[str]
    current_question: Optional[str]

class ChatHistory(BaseModel):
    chat_history: list
        
@app.get("/", response_class=HTMLResponse)
def read_index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MALI_NURSE API</title>
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

model_cache = {}
def get_model_cached(model_name):
    if model_name not in model_cache:
        model_cache[model_name] = get_model(model_name=model_name)
    return model_cache[model_name]

@app.post("/nurse_response")
def nurse_response(user_input: UserInput):
    """
    Models: "typhoon-v1.5x-70b-instruct (default)", "openthaigpt", "llama-3.3-70b-versatile"
    """
    
    start_time = time.time()
    if user_input.model_name != nurse_llm.model_name:
        print(f"Changing model to {user_input.model_name}")
        try:
            nurse_llm.client = get_model_cached(model_name=user_input.model_name)
        except ValueError:
            return {"error": "Invalid model name"}
    print(nurse_llm.client)
    
    # response = nurse_llm.slim_invoke(user_input.user_input)
    response = nurse_llm.invoke(user_input.user_input)
    end_time = time.time()
    duration = end_time - start_time
    print(f"Function running time: {duration} seconds")
    # Log the model name, user input, response, and execution time in CSV format
    with open("runtime_log.csv", "a") as log_file:
        log_file.write(f"{user_input.model_name},{user_input.user_input},{response},{duration}\n")
    
    return NurseResponse(nurse_response=response)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)