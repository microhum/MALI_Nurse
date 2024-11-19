from llm.client import NurseCLI
from llm.llm import VirtualNurseLLM
from dotenv import load_dotenv
import os

load_dotenv()

if __name__ == "__main__":
    model_choice = input("Choose the model to use (1 for typhoon-v1.5x-70b-instruct, 2 for OpenThaiGPT): ")
    if model_choice == "1":
        nurse_llm = VirtualNurseLLM(
            base_url="https://api.opentyphoon.ai/v1",
            model="typhoon-v1.5x-70b-instruct",
            api_key=os.environ.get("TYPHOON_CHAT_KEY")
        )
    elif model_choice == "2":
        nurse_llm = VirtualNurseLLM(
            base_url="https://api.aieat.or.th/v1",
            model="OpenThaiGPT",
            api_key="dummy"
        )
    else:
        print("Invalid choice. Exiting.")
        exit(1)

    cli = NurseCLI(nurse_llm)
    cli.start()