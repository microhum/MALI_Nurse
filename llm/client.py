from pprint import pprint
from llm.llm import VirtualNurseLLM

class NurseCLI:
    def __init__(self, nurse_llm: VirtualNurseLLM):
        self.nurse_llm = nurse_llm
        self.nurse_llm.debug = False

    def start(self):
        print("Welcome to the Nurse LLM CLI.")
        print("Type your question, or enter 'history' to see chat history")
        print("Enter 'help' for a list of available commands.")

        while True:
            user_input = input("\nYou: ")

            if user_input.lower() == 'exit':
                print("Exiting the CLI. Goodbye!")
                break
            elif user_input.lower() == 'history':
                print("\n--- Chat History ---")
                pprint(self.nurse_llm.chat_history)
            elif user_input.lower() == 'ehr':
                print("\n--- Current EHR Data ---")
                pprint(self.nurse_llm.ehr_data)
            elif user_input.lower() == 'status':
                print("\n--- Current LLM Status ---")
                pprint(self.nurse_llm.current_prompt)
            elif user_input.lower() == 'debug':
                self.nurse_llm.debug = not self.nurse_llm.debug
                print(f"Debug mode is now {'on' if self.nurse_llm.debug else 'off'}.")
            elif user_input.lower() == 'reset':
                self.nurse_llm.reset()
                print("Chat history and EHR data have been reset.")
            elif user_input.lower() == 'help':
                self.display_help()
            else:
                # Invoke the LLM with the user input and get the response
                ehr_response = self.nurse_llm.invoke(user_input)

                # Display the response from the nurse LLM
                print("\nNurse LLM:", ehr_response)

    def display_help(self):
        print("""
        --- Available Commands ---
        - 'history'   : View the chat history.
        - 'ehr'       : View the current EHR (Electronic Health Record) data.
        - 'status'    : View the current LLM status and prompt.
        - 'debug'     : Toggle the debug mode (on/off).
        - 'reset'     : Reset the chat history and EHR data.
        - 'help'      : Display this help message.
        - 'exit'      : Exit the CLI.
        """)



