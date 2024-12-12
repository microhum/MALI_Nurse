import uvicorn
from main import app
from interface import create_gradio_interface
import gradio as gr

if __name__ == "__main__":
    gr_interface = create_gradio_interface()
    gr_interface.queue(default_concurrency_limit=1)
    app = gr.mount_gradio_app(app, gr_interface, path="/")
    uvicorn.run(app, host='0.0.0.0', port=7860, workers=1)