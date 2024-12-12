import os
import gradio as gr
import requests

PORT = 7860
API_BASE_URL = f"http://localhost:{PORT}" 

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
        time.sleep(2.5)
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

# --------------------------------------------------------------------------------------------
def call_botnoi_tts(text, speaker, volume, speed):
    url = f"{API_BASE_URL}/tts/generate_voice_botnoi/"
    payload = {
        "text": text,
        "speaker": speaker,
        "volume": volume,
        "speed": speed,
        "token": os.getenv("BOTNOI_API_TOKEN")
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.content, "output.mp3"
    else:
        return f"Error: {response.status_code} - {response.json().get('detail', 'Unknown error')}", None

# Helper function to call VAJA9 API
def call_vaja9_tts(text, speaker, phrase_break, audiovisual):
    url = f"{API_BASE_URL}/tts/generate_voice_vaja9/"
    payload = {
        "text": text,
        "speaker": speaker,
        "phrase_break": phrase_break,
        "audiovisual": audiovisual
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.content, "output.wav"
    else:
        return f"Error: {response.status_code} - {response.json().get('detail', 'Unknown error')}", None
# --------------------------------------------------------------------------------------------

def gradio_tts_interface():
    with gr.Tabs() as tabs:
            # Tab for Botnoi TTS API
            with gr.TabItem("Botnoi TTS"):
                gr.Markdown("### Generate Voice with Botnoi API")

                botnoi_text = gr.Textbox(label="Text", placeholder="Enter text to synthesize")
                botnoi_speaker = gr.Textbox(label="Speaker ID", value="52", placeholder="Default: 52")
                botnoi_volume = gr.Slider(label="Volume", minimum=0, maximum=100, value=100)
                botnoi_speed = gr.Slider(label="Speed", minimum=0.5, maximum=2.0, step=0.1, value=1.0)

                botnoi_generate = gr.Button("Generate Audio")
                botnoi_output = gr.Audio(label="Generated Audio")
                botnoi_error = gr.Textbox(label="Error", interactive=False, visible=False)

                def generate_botnoi_voice(text, speaker, volume, speed):
                    result, file_name = call_botnoi_tts(text, speaker, volume, speed)
                    if file_name:
                        return gr.update(value=result), ""
                    else:
                        return None, result

                botnoi_generate.click(generate_botnoi_voice, 
                                    inputs=[botnoi_text, botnoi_speaker, botnoi_volume, botnoi_speed], 
                                    outputs=[botnoi_output, botnoi_error])

            # Tab for VAJA9 TTS API
            with gr.TabItem("VAJA9 TTS"):
                gr.Markdown("### Generate Voice with VAJA9 API")

                vaja9_text = gr.Textbox(label="Text", placeholder="Enter text to synthesize")
                vaja9_speaker = gr.Radio(label="Speaker", choices=["0 - Male", "1 - Female", "2 - Boy", "3 - Girl"], value="1 - Female")
                vaja9_phrase_break = gr.Radio(label="Phrase Break", choices=["0 - Auto", "1 - None"], value="0 - Auto")
                vaja9_audiovisual = gr.Radio(label="Audiovisual", choices=["0 - Audio", "1 - Audio + Visual"], value="0 - Audio")

                vaja9_generate = gr.Button("Generate Audio")
                vaja9_output = gr.Audio(label="Generated Audio")
                vaja9_error = gr.Textbox(label="Error", interactive=False, visible=False)

                def generate_vaja9_voice(text, speaker, phrase_break, audiovisual):
                    speaker_id = int(speaker.split(" - ")[0])
                    phrase_break_id = int(phrase_break.split(" - ")[0])
                    audiovisual_id = int(audiovisual.split(" - ")[0])

                    result, file_name = call_vaja9_tts(text, speaker_id, phrase_break_id, audiovisual_id)
                    if file_name:
                        return gr.update(value=result), ""
                    else:
                        return None, result

                vaja9_generate.click(generate_vaja9_voice, 
                                    inputs=[vaja9_text, vaja9_speaker, vaja9_phrase_break, vaja9_audiovisual], 
                                    outputs=[vaja9_output, vaja9_error])
    return tabs

# --------------------------------------------------------------------------------------------
# Chatbot Interface
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
            with gr.Column(scale=2):
                chat_box = gr.Chatbot(label="Chat with MALI Nurse", scale=1)
                send_button = gr.Button("Send", variant="primary", size="lg", scale=1)
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
                    
            with gr.Column(scale=1):
                output_selector = gr.Dropdown(
                choices=["Chat History", "EHR Details"],
                value="Chat History",
                label="Select Output to Display",
                )

                chat_history_output = gr.Textbox(
                    label="Chat History Output",
                    interactive=False,
                    lines=6,
                    scale=1,
                    visible=True,  # Initially visible
                )

                ehr_details_output = gr.Textbox(
                    label="EHR Details Output",
                    interactive=False,
                    lines=6,
                    scale=1,
                    visible=False,  # Initially hidden
                )

                # Function to toggle visibility
                def switch_output(selected_output):
                    if selected_output == "Chat History":
                        return gr.update(visible=True), gr.update(visible=False)
                    elif selected_output == "EHR Details":
                        return gr.update(visible=False), gr.update(visible=True)

                # Set up the change event
                output_selector.change(
                    fn=switch_output,
                    inputs=[output_selector],
                    outputs=[chat_history_output, ehr_details_output],  # Update visibility of both components
                )

                notification_box = gr.Textbox(label="Error", interactive=False, lines=2)

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
            send_button.click(
            fn=view_chat_history,
                inputs=[],
                outputs=chat_history_output,
            )
            send_button.click(
                fn=view_ehr_details,
                inputs=[gr.Textbox(value="details", visible=False)],
                outputs=ehr_details_output
            )

            send_button.click(
                fn=view_ehr_details,
                inputs=[gr.Textbox(value="prompt", visible=False)],
                outputs=ehr_prompt_output
            )         

        gr.Markdown(
                """
                ---  
                """
            )
    # TTS --------------------------------------------------------------------------------------------
        gr.Markdown("# Text-to-Speech (TTS) API Test Interface")
        tts_interface = gradio_tts_interface()

        # Footer
        gr.Markdown(
            """
            ---  
            Built With ❤️ by **[Piang](https://github.com/microhum)** 🚀
            Powered by Typhoon v1.5x and OpenThaiGPT Models.  
            """
        )
        
    return interface

# Run the Gradio Interface
if __name__ == "__main__":
    gr_interface = create_gradio_interface()
    gr_interface.launch(server_name="0.0.0.0", server_port=7860)
