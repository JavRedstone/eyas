"""Launcher for the Eyas prototype."""

import gradio as gr
from ui.gradio_app import _CSS, build_app

_THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.emerald,
    neutral_hue=gr.themes.colors.slate,
)

app = build_app()

if __name__ == "__main__":
    app.launch(theme=_THEME, css=_CSS)
