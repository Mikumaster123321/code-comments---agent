# -*- coding: utf-8 -*-
"""Gradio 界面模块：构建美观的 Web 交互界面"""
import gradio as gr
from processor import process_code, analyze_code, handle_file_upload

# ==================== 自定义 CSS ====================
CUSTOM_CSS = """
/* ===== 全局字体与背景 ===== */
.gradio-container {
    font-family: 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif !important;
    max-width: 1400px !important;
    background: linear-gradient(135deg, #f0f4f8 0%, #e8edf5 100%) !important;
}

/* ===== 渐变标题栏 ===== */
.app-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-radius: 16px !important;
    padding: 28px 36px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.35) !important;
    color: white !important;
}
.app-header h1, .app-header h2 {
    color: white !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}
.app-header p {
    color: rgba(255,255,255,0.9) !important;
    margin-top: 8px !important;
    font-size: 15px !important;
}

/* ===== 卡片容器 ===== */
.card-section {
    background: white !important;
    border-radius: 14px !important;
    padding: 20px 24px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    border: 1px solid rgba(0,0,0,0.04) !important;
    transition: box-shadow 0.3s ease !important;
}
.card-section:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
}

/* ===== 代码编辑器容器 ===== */
.code-container .cm-editor {
    max-height: 480px !important;
    overflow-y: auto !important;
    border-radius: 10px !important;
    font-size: 13.5px !important;
}
.code-container .cm-scroller {
    max-height: 480px !important;
    overflow-y: auto !important;
}

/* ===== Markdown 滚动容器 ===== */
.scrollable-md .prose,
.scrollable-md .markdown-body {
    max-height: 480px !important;
    overflow-y: auto !important;
    padding: 4px 8px !important;
}

/* ===== 自定义滚动条 ===== */
.code-container .cm-scroller::-webkit-scrollbar,
.scrollable-md .prose::-webkit-scrollbar {
    width: 8px !important;
}
.code-container .cm-scroller::-webkit-scrollbar-track,
.scrollable-md .prose::-webkit-scrollbar-track {
    background: #f1f1f1 !important;
    border-radius: 4px !important;
}
.code-container .cm-scroller::-webkit-scrollbar-thumb,
.scrollable-md .prose::-webkit-scrollbar-thumb {
    background: #c1c1c1 !important;
    border-radius: 4px !important;
}
.code-container .cm-scroller::-webkit-scrollbar-thumb:hover,
.scrollable-md .prose::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8 !important;
}

/* ===== 按钮样式 ===== */
.action-btn {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 3px 12px rgba(0,0,0,0.1) !important;
}
.action-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
}

/* ===== Tab 样式 ===== */
.gradio-container .tab-nav {
    border-bottom: 2px solid #e0e0e0 !important;
    gap: 4px !important;
}
.gradio-container .tab-nav button {
    border-radius: 10px 10px 0 0 !important;
    padding: 10px 20px !important;
    font-weight: 500 !important;
    color: #666 !important;
    transition: all 0.2s ease !important;
}
.gradio-container .tab-nav button:hover {
    background: rgba(102, 126, 234, 0.08) !important;
    color: #667eea !important;
}
.gradio-container .tab-nav button.selected {
    border-bottom: 3px solid #667eea !important;
    color: #667eea !important;
    font-weight: 700 !important;
    background: rgba(102, 126, 234, 0.05) !important;
}

/* ===== 输入组件圆角 ===== */
.gradio-container input[type="text"],
.gradio-container textarea,
.gradio-container .gr-file {
    border-radius: 8px !important;
}

/* ===== 标签文字 ===== */
.gradio-container label {
    font-weight: 500 !important;
    color: #444 !important;
}

/* ===== 等宽列 ===== */
.equal-width > div {
    flex: 1 !important;
}

/* ===== 复选框样式 ===== */
.gradio-container input[type="checkbox"] {
    accent-color: #667eea !important;
}

/* ===== 下拉框样式 ===== */
.gradio-container select,
.gradio-container .gr-dropdown {
    border-radius: 8px !important;
}

/* ===== 页脚 ===== */
.app-footer {
    text-align: center !important;
    padding: 16px !important;
    color: #999 !important;
    font-size: 13px !important;
    margin-top: 8px !important;
}
"""


def _update_file_types(language: str):
    """根据语言切换文件上传组件接受的扩展名

    Args:
        language: 编程语言名称

    Returns:
        gr.update: Gradio 更新对象
    """
    if language == "Java":
        return gr.update(file_types=[".java"])
    return gr.update(file_types=[".py"])


def _update_code_language(language: str):
    """根据语言切换代码编辑器的语法高亮

    Args:
        language: 编程语言名称

    Returns:
        gr.update: Gradio 更新对象
    """
    return gr.update(language="java" if language == "Java" else "python")


def create_ui():
    """创建并返回 Gradio 界面对象

    Returns:
        gr.Blocks: 配置好的 Gradio 界面实例
    """
    with gr.Blocks(title="代码注释 Agent") as demo:
        # ===== 标题栏 =====
        with gr.Column(elem_classes="app-header"):
            gr.Markdown("# 📝 代码注释与 API 文档自动生成 Agent")
            gr.Markdown("粘贴代码或上传文件，AI 自动生成中文注释和 Markdown API 文档  ·  支持 Python & Java")

        # ===== 语言选择 =====
        with gr.Column(elem_classes="card-section"):
            with gr.Row():
                language = gr.Dropdown(
                    choices=["Python", "Java"], value="Python",
                    label="🌐 编程语言", scale=3,
                )
                incremental_chk = gr.Checkbox(
                    label="增量更新模式（跳过已有注释的函数，节省 API 调用）",
                    value=False, scale=7,
                )

        # ===== 输入区 =====
        with gr.Column(elem_classes="card-section"):
            gr.Markdown("### 📥 代码输入")
            with gr.Row(equal_height=True):
                with gr.Column(elem_classes="equal-width", scale=1):
                    file_upload = gr.File(
                        label="上传源代码文件",
                        file_types=[".py", ".java"],
                    )
                with gr.Column(elem_classes="equal-width", scale=2):
                    input_box = gr.Code(
                        label="✏️ 代码编辑器（粘贴或上传文件后自动填充）",
                        language="python", lines=22, max_lines=22,
                        elem_classes="code-container",
                    )

        # ===== 操作按钮 =====
        with gr.Row():
            btn = gr.Button("🚀 生成注释与文档", variant="primary", size="lg",
                            elem_classes="action-btn")
            analyze_btn = gr.Button("🔍 分析代码", variant="secondary", size="lg",
                                    elem_classes="action-btn")

        # ===== 输出区 =====
        with gr.Column(elem_classes="card-section"):
            with gr.Tabs():
                with gr.Tab("📄 带注释的代码"):
                    output_code = gr.Code(
                        label="带注释的代码",
                        language="python", lines=22, max_lines=22,
                        elem_classes="code-container",
                    )
                    with gr.Row():
                        download_src = gr.File(label="⬇️ 下载注释后的代码", scale=1)
                        download_md = gr.File(label="⬇️ 下载 API 文档 (.md)", scale=1)
                with gr.Tab("📚 API 文档"):
                    output_docs = gr.Markdown(
                        label="生成的 API 文档",
                        elem_classes="scrollable-md",
                    )
                with gr.Tab("🔍 代码分析"):
                    quality_output = gr.Markdown(
                        label="代码质量分析",
                        elem_classes="scrollable-md",
                    )
                    annotation_output = gr.Markdown(
                        label="类型注解检查",
                        elem_classes="scrollable-md",
                    )
                    summary_output = gr.Markdown(
                        label="代码摘要",
                        elem_classes="scrollable-md",
                    )
                    analyze_log = gr.Textbox(label="分析日志", lines=4, max_lines=4)
                with gr.Tab("📋 处理日志"):
                    output_log = gr.Textbox(label="处理日志", lines=12, max_lines=12)

        # ===== 页脚 =====
        gr.Markdown("Powered by DeepSeek LLM  ·  Gradio 6.0  ·  自动生成中文注释与文档",
                    elem_classes="app-footer")

        # ===== 事件绑定 =====
        file_upload.change(fn=handle_file_upload, inputs=file_upload, outputs=input_box)
        language.change(fn=_update_file_types, inputs=language, outputs=file_upload)
        language.change(fn=_update_code_language, inputs=language, outputs=input_box)
        language.change(fn=_update_code_language, inputs=language, outputs=output_code)
        btn.click(
            fn=process_code,
            inputs=[input_box, incremental_chk, language],
            outputs=[output_code, output_docs, output_log, download_md, download_src],
        )
        analyze_btn.click(
            fn=analyze_code,
            inputs=[input_box, language],
            outputs=[quality_output, annotation_output, summary_output, analyze_log],
        )

    return demo
