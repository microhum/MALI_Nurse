from llm.client import NurseCLI
from llm.llm import VirtualNurseLLM

# model: typhoon-v1.5x-70b-instruct
# nurse_llm = VirtualNurseLLM(
#     base_url="https://api.opentyphoon.ai/v1",
#     model="typhoon-v1.5x-70b-instruct",
#     api_key=os.getenv("TYPHOON_API_KEY")
# )

# model: OpenThaiGPT

if __name__ == "__main__":
    nurse_llm = VirtualNurseLLM(
    base_url="https://api.aieat.or.th/v1",
    model=".",
    api_key="dummy"
    )

    cli = NurseCLI(nurse_llm)
    cli.start()