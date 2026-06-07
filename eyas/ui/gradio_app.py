"""Minimal Gradio app scaffold for the Eyas prototype.

Implement UI wiring to call the processing pipeline modules.
"""
import gradio as gr


def build_app():
    with gr.Blocks() as demo:
        gr.Markdown("## Eyas — CCTV Security Assistant (prototype)")
        with gr.Row():
            inp = gr.File(label="Upload video clip")
            run = gr.Button("Process")
        out = gr.Textbox(label="Summary")

        def _process(file_obj):
            # TODO: call pipeline (detection, processing, event structuring, LLM)
            return "(prototype) no processing implemented"

        run.click(_process, inputs=inp, outputs=out)
    return demo
