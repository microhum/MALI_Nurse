
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from pydantic import ValidationError
import json
from pprint import pprint
from llm.basemodel import EHRModel
from llm.prompt import field_descriptions, TASK_INSTRUCTIONS, JSON_EXAMPLE

class VirtualNurseLLM:
    def __init__(self, base_url, model, api_key):
        self.client = ChatOpenAI(
            base_url=base_url,
            model=model,
            api_key=api_key
        )
        self.TASK_INSTRUCTIONS = TASK_INSTRUCTIONS
        self.field_descriptions = field_descriptions
        self.JSON_EXAMPLE = JSON_EXAMPLE
        self.ehr_data = {}
        self.chat_history = []
        self.current_patient_response = None
        self.current_context = None
        self.debug = False
        self.current_prompt = None
        self.current_prompt_ehr = None
        self.current_question = None

    def create_prompt(self, task_type):
        if task_type == "extract_ehr":
          system_instruction = self.TASK_INSTRUCTIONS.get("extract_ehr")

        elif task_type == "question":
          system_instruction = self.TASK_INSTRUCTIONS.get("question")
        else:
          raise ValueError("Invalid task type.")

        # system + user
        system_template = SystemMessagePromptTemplate.from_template(system_instruction)
        user_template = HumanMessagePromptTemplate.from_template("response: {patient_response}")
        prompt = ChatPromptTemplate.from_messages([system_template, user_template])
        return prompt

    def gather_ehr(self, patient_response, max_retries=3):
        prompt = self.create_prompt("extract_ehr")
        messages = prompt.format_messages(ehr_data=self.ehr_data, patient_response=patient_response, example=self.JSON_EXAMPLE)
        self.current_prompt_ehr = messages[0].content
        response = self.client(messages=messages)
        if self.debug:
            pprint(f"gather ehr llm response: \n{response.content}\n")
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                json_content = self.extract_json_content(response.content)
                if self.debug:
                    pprint(f"JSON after dumps:\n{json_content}\n")
                ehr_data = EHRModel.model_validate_json(json_content)

                # Update only missing parameters
                for key, value in ehr_data.model_dump().items():
                    if value not in [None, [], {}]:  # Checks for None and empty lists or dicts
                        print(f"Updating {key} with value {value}")
                        self.ehr_data[key] = value

                return self.ehr_data

            except (ValidationError, json.JSONDecodeError) as e:
                print(f"Error parsing EHR data: {e}")
                retry_count += 1

                if retry_count < max_retries:
                    retry_prompt = (
                        "กรุณาตรวจสอบให้แน่ใจว่าข้อมูลที่ให้มาอยู่ในรูปแบบ JSON ที่ถูกต้องตามโครงสร้างตัวอย่าง "
                        "และแก้ไขปัญหาทางไวยากรณ์หรือรูปแบบที่ไม่ถูกต้อง รวมถึงให้ข้อมูลในรูปแบบที่สอดคล้องกัน "
                        f"Attempt {retry_count + 1} of {max_retries}."
                    )
                    messages = self.create_prompt("extract_ehr") + "\n\n# ลองใหม่: \n\n{retry_prompt} \n ## JSON เก่าที่มีปัญหา: \n{json_problem}"
                    messages = messages.format_messages(
                        patient_response=patient_response, 
                        example=self.JSON_EXAMPLE, 
                        retry_prompt=retry_prompt,
                        json_problem=json_content
                    )
                    self.current_prompt_ehr = messages[0].content
                    print(f"กำลังลองใหม่ด้วย prompt ที่ปรับแล้ว: {retry_prompt}")
                    response = self.client(messages=messages)

        # Final error message if retries are exhausted
        print("Failed to extract valid EHR data after multiple attempts. Generating new question.")
        return {"result": response, "error": "Failed to extract valid EHR data. Please try again."}


    def get_question(self, patient_response):
        question_prompt = self.create_prompt("question")
        # Update EHR data with the latest patient response
        ehr_data = self.gather_ehr(patient_response)
        if self.debug:
            pprint(ehr_data)

        for field, description in self.field_descriptions.items():
            # Find the next missing field and generate a question
            if field not in self.ehr_data or not self.ehr_data[field]:
                # Compile known patient information as context
                context = ", ".join(
                    f"{key}: {value}" for key, value in self.ehr_data.items() if value
                )
                print("fetching for ", f'"{field}":"{description}"')
                history_context = "\n".join(
                    f"{entry['role']}: {entry['content']}" for entry in self.chat_history
                )
                messages = ChatPromptTemplate.from_messages([question_prompt, history_context])
                messages = messages.format_messages(description=f'"{field}":"{description}"', context=context, patient_response=patient_response, field_descriptions=self.field_descriptions)
                self.current_context = context
                self.current_prompt = messages[0].content
                
                # format print
                # pprint(pformat(messages.messages[0].prompt.template, indent=4, width=80))
                response = self.client(messages=messages)

                # Store generated question in chat history and return it
                self.current_question = response.content.strip()
                return self.current_question

        # If all fields are complete
        self.current_question = "ขอบคุณที่ให้ข้อมูลค่ะ ฉันได้ข้อมูลที่ต้องการครบแล้วค่ะ"
        return self.current_question

    def invoke(self, patient_response):
        if patient_response:
            self.chat_history.append({"role": "user", "content": patient_response})
        question = self.get_question(patient_response)
        self.current_patient_response = patient_response
        self.chat_history.append({"role": "assistant", "content": question})
        return question

    def extract_json_content(self, content):
        try:
            content = content.replace('\n', '').replace('\r', '')
            start = content.index('{')
            end = content.rindex('}') + 1
            json_str = content[start:end]
            json_str = json_str.replace('None', 'null')

            return json_str
        except ValueError:
            print("JSON Parsing Error Occured: ", content)
            print("No valid JSON found in response")
            return None


    def reset(self):
        self.ehr_data = {}
        self.chat_history = []
        self.current_question = None