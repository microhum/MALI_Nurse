from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from pydantic import ValidationError
import json
from pprint import pprint
from llm.basemodel import EHRModel
from llm.prompt import field_descriptions, TASK_INSTRUCTIONS, JSON_EXAMPLE
from llm.models import get_model
import time

class VirtualNurseLLM:
    def __init__(self, base_url=None, model_name=None, api_key=None, model_type=None):
        self.client = None
        if model_name:
            self.client = get_model(model_name=model_name)
        self.model_name = model_name
        self.TASK_INSTRUCTIONS = TASK_INSTRUCTIONS
        self.field_descriptions = field_descriptions
        self.JSON_EXAMPLE = JSON_EXAMPLE
        self.ehr_data = {}
        self.chat_history = []
        self.chat_history.append({"role": "assistant", "content": "สวัสดีค่ะ ดิฉัน มะลิ เป็นพยาบาลเสมือนที่จะมาดูแลการซักประวัตินะคะ"})
        self.current_patient_response = None
        self.current_context = None
        self.debug = False
        self.current_prompt = None
        self.current_prompt_ehr = None
        self.current_question = None
        self.ending_text = "ขอบคุณที่ให้ข้อมูลค่ะ ฉันได้ข้อมูลที่ต้องการครบแล้วค่ะ ดิฉันจะบันทึกข้อมูลทั้งหมดนี้เพื่อส่งต่อให้แพทย์ดูแลคุณอย่างเหมาะสมค่ะ"
        
    def create_prompt(self, task_type):
        if task_type == "extract_ehr":
          system_instruction = self.TASK_INSTRUCTIONS.get("extract_ehr")

        elif task_type == "question":
          system_instruction = self.TASK_INSTRUCTIONS.get("question")

        elif task_type == "refactor":
          system_instruction = self.TASK_INSTRUCTIONS.get("refactor")

        else:
          raise ValueError("Invalid task type.")

        # system + user
        system_template = SystemMessagePromptTemplate.from_template(system_instruction)
        user_template = HumanMessagePromptTemplate.from_template("response: {patient_response}")
        prompt = ChatPromptTemplate.from_messages([system_template, user_template])
        return prompt

    def gather_ehr(self, patient_response, max_retries=2):
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
                print(f"Error parsing EHR data: {e} Retrying {retry_count}...")
                retry_count += 1

                if retry_count < max_retries:
                    retry_prompt = (
                        "กรุณาตรวจสอบให้แน่ใจว่าข้อมูลที่ให้มาอยู่ในรูปแบบ JSON ที่ถูกต้องตามโครงสร้างตัวอย่าง "
                        "และแก้ไขปัญหาทางไวยากรณ์หรือรูปแบบที่ไม่ถูกต้อง รวมถึงให้ข้อมูลในรูปแบบที่สอดคล้องกัน "
                        "ห้ามมีการ hallucination หากไม่เจอข้อมูลให้ใส่ค่า null "
                        f"Attempt {retry_count + 1} of {max_retries}."
                    )
                    messages = self.create_prompt("extract_ehr") + "\n\n# ลองใหม่: \n\n{retry_prompt} \n ## JSON เก่าที่มีปัญหา: \n{json_problem}"
                    messages = messages.format_messages(
                        ehr_data = self.ehr_data,
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

    def fetching_chat(self, patient_response, question_prompt):
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
                messages = messages.format_messages(
                    description=f'"{field}":"{description}"', 
                    context=context, 
                    patient_response=patient_response, 
                    field_descriptions=self.field_descriptions,
                    time_now=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                self.current_context = context
                self.current_prompt = messages[0].content

                start_time = time.time()
                response = self.client(messages=messages)
                print(f"Time after getting response from client: {time.time() - start_time} seconds")

                # Store generated question in chat history and return it
                self.current_question = response.content.strip()
                
                return self.current_question
            
    def refactor_ehr(self, current_question=None):
        patient_response = current_question or self.ending_text
        refactor_prompt = self.create_prompt("refactor")
        messages = ChatPromptTemplate.from_messages([refactor_prompt])
        messages = messages.format_messages(patient_response="", ehr_data=self.ehr_data, chat_history=self.chat_history, time_now=time.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.client(messages=messages)
        json_content = self.extract_json_content(response.content)
        pprint(f"JSON after dumps:\n{json_content}\n")
        self.ehr_data = EHRModel.model_validate_json(json_content)
        print("Refactored EHR data ! Ending the process.")
        return patient_response
    
    def get_question(self, patient_response):
        question_prompt = self.create_prompt("question")
        # Update EHR data with the latest patient response
        start_time = time.time()
        ehr_data = self.gather_ehr(patient_response)
        print(f"Time after gathering EHR: {time.time() - start_time} seconds")

        if self.debug:
            pprint(ehr_data)

        self.current_question = self.fetching_chat(patient_response, question_prompt) or self.refactor_ehr()
        if self.ending_text in self.current_question:
            return self.refactor_ehr(self.current_question)
        return self.current_question

    def invoke(self, patient_response):
        if patient_response:
            self.chat_history.append({"role": "user", "content": patient_response})
        question = self.get_question(patient_response)
        self.current_patient_response = patient_response
        self.chat_history.append({"role": "assistant", "content": question})
        return question
    
    def slim_invoke(self, patient_response):
        start_time = time.time()
        user_message = HumanMessagePromptTemplate.from_template("response: {patient_response}")
        print(f"Time after creating user_message: {time.time() - start_time} seconds")

        start_time = time.time()
        messages = ChatPromptTemplate.from_messages([user_message]).format_messages(patient_response=patient_response)
        print(f"Time after formatting messages: {time.time() - start_time} seconds")

        start_time = time.time()
        response = self.client(messages=messages)
        print(f"Time after getting response from client: {time.time() - start_time} seconds")

        return response.content


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
