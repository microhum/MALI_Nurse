import gradio as gr
import requests

API_BASE_URL = "http://127.0.0.1:8000"  # Update this with your actual API base URL if deployed elsewhere

# Function: Get nurse response
def get_nurse_response(user_input, model_name, chat_history):
    
    try:
        start_time = time.time()
        # Send user input to the API
        response = requests.post(
            f"{API_BASE_URL}/nurse_response",
            json={"user_input": user_input, "model_name": model_name},
            timeout=15
        )
        response.raise_for_status()
        end_time = time.time()
        elapsed_time = end_time - start_time
        nurse_response = response.json().get("nurse_response", "No response received.")

        # Append user and nurse messages to the chat history
        chat_history.append((f"👤 {user_input}", f"🤖 {nurse_response} ({elapsed_time:.2f} s.)"))
        return chat_history, ""  # Clear the user input after sending
    except requests.exceptions.RequestException as e:
        chat_history.append(("⚠️ Error", str(e)))
        return chat_history, ""


# Function: Reset chat history
def reset_history():
    response = requests.post(f"{API_BASE_URL}/reset")
    return [], "", response.text

# Function: View chat history
def view_chat_history():
    try:    
        response = requests.get(f"{API_BASE_URL}/history")
        response.raise_for_status()
        chat_history = response.json().get("chat_history", [])
        if not chat_history:
            return "No chat history available."
        
        # Properly format chat history for display
        formatted_history = []
        for message in chat_history:
            if message.get("role") == "user":
                formatted_history.append(f"👤 User: {message.get('content', '')}")
            elif message.get("role") == "assistant":
                formatted_history.append(f"🤖 Nurse: {message.get('content', '')}")

        return "\n".join(formatted_history)
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

import json
import time
# Function: View EHR details
def view_ehr_details(view):
    try:
        response = requests.get(f"{API_BASE_URL}/details")
        response.raise_for_status()
        ehr_data = response.json()
        if view == "details":
            ehr_data = ehr_data["ehr_data"]
        elif view == "prompt":
            ehr_data.pop("ehr_data", None)
        ehr_data = json.dumps(ehr_data, indent=4, ensure_ascii=False)
        return ehr_data
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

# Gradio Interface
def create_gradio_interface():
    with gr.Blocks() as interface:
        # Title and description
        gr.Markdown(
            """
            # MALI_NURSE Gradio Interface
            ### A User-Friendly Interface to Interact with the MALI_NURSE API
            Select a model, input your question, and view nurse responses or manage chat history and EHR details.
            """
        )

        # Main Input Section
        with gr.Row():
           with gr.Row():
            chat_box = gr.Chatbot(label="Chat with MALI Nurse")

        # Input Section
        with gr.Row():
            user_input = gr.Textbox(
                label="Your Message",
                placeholder="Type your question or message here...",
                lines=2,
            )
            model_name = gr.Radio(
                choices=["typhoon-v1.5x-70b-instruct", "openthaigpt", "llama-3.3-70b-versatile"],
                value="typhoon-v1.5x-70b-instruct",
                label="Model Selection",
            )
            with gr.Column():
                send_button = gr.Button("Send", variant="primary", size="lg")
                notification_box = gr.Textbox(interactive=False, lines=2)

        # Bind Get Nurse Response button
        send_button.click(
            fn=get_nurse_response,
            inputs=[user_input, model_name, chat_box],
            outputs=[chat_box, user_input],  # Update chat box and clear input
        )

        # Advanced Options
        with gr.Accordion("Advanced Options", open=False):
            with gr.Row():
                reset_button = gr.Button("Reset Data", variant="primary")
                chat_history_button = gr.Button("View Chat History")
                ehr_details_button = gr.Button("View EHR Details")
            with gr.Column():
                chat_history_output = gr.Textbox(
                    label="Chat History",
                    interactive=False,
                    lines=6,
                )
                ehr_details_output = gr.Textbox(
                    label="EHR Details",
                    interactive=False,
                    lines=6,
                )
                ehr_prompt_output = gr.Textbox(
                    label="Outputs",
                    interactive=False,
                    lines=6,
                )

            # Bind buttons to respective functions
            reset_button.click(
            fn=reset_history,
            inputs=[],
            outputs=[chat_box, user_input, notification_box],  # Clear chat box and input
        )
            chat_history_button.click(
                fn=view_chat_history,
                inputs=[],
                outputs=chat_history_output,
            )
            # View EHR Details
            ehr_details_button.click(
                fn=view_ehr_details,
                inputs=[gr.Textbox(value="details", visible=False)],
                outputs=ehr_details_output
            )
            ehr_details_button.click(
                fn=view_ehr_details,
                inputs=[gr.Textbox(value="prompt", visible=False)],
                outputs=ehr_prompt_output
            )            

        # Footer
        gr.Markdown(
            """
            ---  
            Developed by **Piang** 🚀  
            Powered by Typhoon v1.5x and OpenThaiGPT Models.  
            """
        )

    return interface

# Run the Gradio Interface
if __name__ == "__main__":
    gr_interface = create_gradio_interface()
    gr_interface.launch(server_name="0.0.0.0", server_port=7860)
