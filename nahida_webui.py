import os
import time
from pathlib import Path

import gradio as gr

from nahida_tts import DEFAULT_OUTPUT_DIR, NahidaTTS


ENGINE = NahidaTTS()


def load_model() -> str:
    try:
        ENGINE.load()
    except Exception as error:
        return f"模型加载失败: {error}"
    return f"模型已加载，设备: {ENGINE.device}"


def generate(text: str) -> tuple[str | None, str]:
    if not text or not text.strip():
        return None, "请输入文本"

    output = DEFAULT_OUTPUT_DIR / f"nahida_{time.strftime('%Y%m%d_%H%M%S')}.wav"
    try:
        result = ENGINE.generate(text=text, output_path=output)
    except Exception as error:
        return None, f"生成失败: {error}"

    status = (
        f"生成完成 | {result.duration_seconds:.2f} 秒 | "
        f"{result.sample_rate} Hz | {result.elapsed_seconds:.2f} 秒"
    )
    return str(result.output_path), status


with gr.Blocks(title="纳西妲 TTS") as app:
    gr.Markdown("# 纳西妲 TTS")
    status = gr.Textbox(label="状态", interactive=False, value="模型未加载")
    text = gr.Textbox(label="文本", lines=8)
    with gr.Row():
        load_button = gr.Button("加载模型")
        generate_button = gr.Button("生成语音", variant="primary")
    audio = gr.Audio(label="生成结果", type="filepath")

    load_button.click(load_model, outputs=status)
    generate_button.click(generate, inputs=text, outputs=[audio, status])


if __name__ == "__main__":
    app.queue(default_concurrency_limit=1).launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7861")),
        inbrowser=os.getenv("GRADIO_INBROWSER", "1") == "1",
        allowed_paths=[str(Path(DEFAULT_OUTPUT_DIR).resolve())],
    )
