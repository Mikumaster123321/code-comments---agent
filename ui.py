# -*- coding: utf-8 -*-
"""Gradio 界面模块：构建 Web 交互界面"""
import gradio as gr
from processor import process_code, analyze_code, handle_file_upload

# 自定义 CSS：限制组件高度，强制滚动，统一布局
CUSTOM_CSS = """
/* 限制 Code 组件的高度，强制内部内容滚动 */
.code-container .cm-editor,
.code-container .cm-scroller {
    max-height: 500px !important;
    overflow-y: auto !important;
}

/* 限制 Markdown 组件的高度，强制内容滚动 */
.scrollable-md .prose,
.scrollable-md .markdown-body {
    max-height: 500px !important;
    overflow-y: auto !important;
}

/* 统一左右栏宽度 */
.equal-width > div {
    flex: 1 !important;
}
"""


def create_ui():
    """创建并返回 Gradio 界面对象

    Returns:
        gr.Blocks: 配置好的 Gradio 界面实例
    """
    with gr.Blocks(title="代码注释与文档生成Agent") as demo:
        gr.Markdown("## 📝 代码注释与 API 文档自动生成 Agent")
        gr.Markdown("粘贴 Python 代码或上传 .py 文件，自动生成中文注释和 Markdown API 文档。")

        # 顶部：输入区
        with gr.Row(equal_height=True):
            with gr.Column(elem_classes="equal-width"):
                file_upload = gr.File(label="📤 上传 Python 文件 (.py)", file_types=[".py"])
            with gr.Column(elem_classes="equal-width"):
                input_box = gr.Code(
                    label="✏️ 输入代码（粘贴或上传文件后自动填充）",
                    language="python", lines=20, max_lines=20,
                    elem_classes="code-container"
                )

        # 中间：操作按钮
        with gr.Row():
            btn = gr.Button("🚀 生成注释与文档", variant="primary", size="lg")
            analyze_btn = gr.Button("🔍 分析代码", variant="secondary", size="lg")
        with gr.Row():
            incremental_chk = gr.Checkbox(
                label="增量更新模式（跳过已有注释的函数，节省 API 调用）",
                value=False
            )

        # 底部：输出区（Tab 分页）
        with gr.Tabs():
            with gr.Tab("📄 带注释的代码"):
                output_code = gr.Code(
                    label="带注释的代码",
                    language="python", lines=20, max_lines=20,
                    elem_classes="code-container"
                )
                download_py = gr.File(label="⬇️ 下载注释后的代码 (.py)")
            with gr.Tab("📚 API 文档"):
                output_docs = gr.Markdown(label="生成的 API 文档", elem_classes="scrollable-md")
                download_md = gr.File(label="⬇️ 下载 API 文档 (.md)")
            with gr.Tab("🔍 代码分析"):
                gr.Markdown("### 代码质量分析、类型注解检查与摘要生成")
                quality_output = gr.Markdown(label="代码质量分析", elem_classes="scrollable-md")
                annotation_output = gr.Markdown(label="类型注解检查", elem_classes="scrollable-md")
                summary_output = gr.Markdown(label="代码摘要", elem_classes="scrollable-md")
                analyze_log = gr.Textbox(label="分析日志", lines=5, max_lines=5)
            with gr.Tab("📋 处理日志"):
                output_log = gr.Textbox(label="处理日志", lines=10, max_lines=10)

        # 绑定事件
        file_upload.change(fn=handle_file_upload, inputs=file_upload, outputs=input_box)
        btn.click(
            fn=process_code,
            inputs=[input_box, incremental_chk],
            outputs=[output_code, output_docs, output_log, download_md, download_py]
        )
        analyze_btn.click(
            fn=analyze_code,
            inputs=input_box,
            outputs=[quality_output, annotation_output, summary_output, analyze_log]
        )

    return demo
