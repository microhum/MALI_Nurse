import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
load_dotenv()

model_list = {
    "typhoon-v1.5x-70b-instruct": {
        "model_name": "typhoon-v1.5x-70b-instruct",
        "model_type": "openai",
        "base_url": "https://api.opentyphoon.ai/v1",
        "api_key": os.getenv("TYPHOON_CHAT_KEY")
    },
    "openthaigpt": {
        "model_name": ".",
        "model_type": "openai",
        "base_url": "https://api.aieat.or.th/v1",
        "api_key": "dummy"
    },
    "llama-3.3-70b-versatile": {
        "model_name": "llama-3.3-70b-versatile",
        "model_type": "groq",
        "base_url": None,
        "api_key": os.getenv("GROQ_CHAT_KEY")
    }
}

def get_model(model_name, base_url=None, api_key=None):
    api_key = api_key or model_list[model_name]["api_key"]
    base_url = base_url or model_list[model_name]["base_url"]
    model = model_list[model_name]["model_name"]
    model_type = model_list[model_name]["model_type"]
    if model_type == "openai":
        return ChatOpenAI(
            temperature=0.3,
            timeout=15,
            base_url= base_url, model=model, api_key=api_key, max_retries=0)
    elif model_type == "groq":
        return ChatGroq(temperature=0.3, timeout=15, groq_api_key=api_key, model_name=model,max_retries=0)
    else:
        raise ValueError("Invalid model type. Supported types are 'openai' and 'groq'.")