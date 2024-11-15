import uvicorn
from llm.llm import VirtualNurseLLM
from fastapi import FastAPI
from pydantic import BaseModel
import os
import dotenv
dotenv.load_dotenv()

# model: typhoon-v1.5x-70b-instruct
# nurse_llm = VirtualNurseLLM(
#     base_url="https://api.opentyphoon.ai/v1",
#     model="typhoon-v1.5x-70b-instruct",
#     api_key=os.getenv("TYPHOON_API_KEY")
# )

# model: OpenThaiGPT
nurse_llm = VirtualNurseLLM(
    base_url="https://api.aieat.or.th/v1",
    model=".",
    api_key="dummy"
)

app = FastAPI()

class UserInput(BaseModel):
    user_input: str

@app.get("/history")
def get_chat_history():
    return {"chat_history": nurse_llm.chat_history}

@app.get("/ehr")
def get_ehr_data():
    return {"ehr_data": nurse_llm.ehr_data}

@app.get("/status")
def get_status():
    return {"current_prompt": nurse_llm.current_prompt}

@app.post("/debug")
def toggle_debug():
    nurse_llm.debug = not nurse_llm.debug
    return {"debug_mode": "on" if nurse_llm.debug else "off"}

@app.post("/reset")
def data_reset():
    nurse_llm.reset()
    print("Chat history and EHR data have been reset.")

@app.post("/nurse_response")
def nurse_response(user_input: UserInput):
    response = nurse_llm.invoke(user_input.user_input)
    return {"nurse_response": response}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)