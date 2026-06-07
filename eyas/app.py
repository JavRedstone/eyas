"""Minimal launcher for the Eyas prototype.

This file is a lightweight scaffold that imports the Gradio app from `ui/gradio_app.py`.
Implement components in their modules and wire them into the UI.
"""

from ui.gradio_app import build_app

app = build_app()

if __name__ == "__main__":
    app.launch()
