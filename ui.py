# -*- coding: utf-8 -*-
"""Gradio 界面模块：构建美观的 Web 交互界面"""
import gradio as gr
from processor import process_code, analyze_code, handle_file_upload

# ==================== 自定义 CSS ====================
CUSTOM_CSS = """
/* ===== 全局基础 ===== */
.gradio-container {
    font-family: 'Inter', 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif !important;
    max-width: 1280px !important;
    padding: 24px 20px !important;
    background: #f5f7fb !important;
    color: #1f2937 !important;
}

/* ===== 顶部导航 ===== */
.app-header {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%) !important;
    border-radius: 16px !important;
    padding: 24px 32px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 10px 40px -10px rgba(79, 70, 229, 0.4) !important;
    color: white !important;
    position: relative !important;
    overflow: hidden !important;
}
.app-header::before {
    content: '' !important;
    position: absolute !important;
    top: -50% !important;
    right: -10% !important;
    width: 300px !important;
    height: 300px !important;
    background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%) !important;
    border-radius: 50% !important;
}
.app-header h1 {
    color: white !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    margin: 0 0 6px 0 !important;
    position: relative !important;
    z-index: 1 !important;
}
.app-header h2, .app-header p {
    color: rgba(255,255,255,0.85) !important;
    margin: 0 !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    position: relative !important;
    z-index: 1 !important;
}

/* ===== 卡片容器 ===== */
.card-section {
    background: white !important;
    border-radius: 12px !important;
    padding: 20px 22px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.03) !important;
    border: 1px solid rgba(0,0,0,0.05) !important;
    transition: box-shadow 0.25s ease, transform 0.25s ease !important;
}
.card-section:hover {
    box-shadow: 0 2px 6px rgba(0,0,0,0.05), 0 8px 24px rgba(0,0,0,0.06) !important;
}

/* ===== 代码编辑器核心修复 ===== */
.code-container {
    height: 650px !important;
    min-height: 400px !important;
    width: 100% !important;
}
/* 关键：让 Gradio Code 内部所有层级继承高度 */
.code-container > div,
.code-container > .code,
.code-container .code,
.code-container .cm-editor,
.code-container .cm-scroller,
.code-container .cm-content {
    height: 100% !important;
    min-height: 400px !important;
    max-height: 650px !important;
}
.code-container .cm-editor {
    border-radius: 10px !important;
    font-size: 14px !important;
    border: 1px solid #d1d5db !important;
    background: #ffffff !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
.code-container .cm-editor.cm-focused {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1), 0 1px 3px rgba(0,0,0,0.04) !important;
}
.code-container .cm-scroller {
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Menlo', monospace !important;
    line-height: 1.6 !important;
    background: #ffffff !important;
    overflow: auto !important;
}
.code-container .cm-content,
.code-container .cm-line,
.code-container .cm-editor,
.code-container.cm-editor {
    background: #ffffff !important;
    color: #1f2937 !important;
}
.code-container .cm-gutters {
    background: #f9fafb !important;
    border-right: 1px solid #e5e7eb !important;
    color: #9ca3af !important;
}
.code-container .cm-activeLine {
    background: #f3f4f6 !important;
}
.code-container .cm-activeLineGutter {
    background: #e5e7eb !important;
    color: #374151 !important;
}

/* ===== 滚动容器 ===== */
.scrollable-md {
    max-height: 600px !important;
    min-height: 300px !important;
    overflow-y: auto !important;
    padding: 12px 16px !important;
    background: white !important;
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
}

/* ===== 美化滚动条 ===== */
.code-container .cm-scroller::-webkit-scrollbar,
.scrollable-md::-webkit-scrollbar {
    width: 10px !important;
    height: 10px !important;
}
.code-container .cm-scroller::-webkit-scrollbar-track,
.scrollable-md::-webkit-scrollbar-track {
    background: transparent !important;
}
.code-container .cm-scroller::-webkit-scrollbar-thumb,
.scrollable-md::-webkit-scrollbar-thumb {
    background: #d1d5db !important;
    border-radius: 5px !important;
    border: 2px solid transparent !important;
    background-clip: content-box !important;
}
.code-container .cm-scroller::-webkit-scrollbar-thumb:hover,
.scrollable-md::-webkit-scrollbar-thumb:hover {
    background: #9ca3af !important;
    background-clip: content-box !important;
    border: 2px solid transparent !important;
}

/* ===== 操作按钮 ===== */
.action-btn {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 28px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: none !important;
    letter-spacing: 0.01em !important;
}
.action-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px -4px rgba(0,0,0,0.15) !important;
}
.action-btn:active {
    transform: translateY(0) !important;
}

/* ===== Tab 美化 ===== */
.gradio-container .tab-nav {
    border-bottom: 1px solid #e5e7eb !important;
    gap: 2px !important;
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
}
.gradio-container .tab-nav button {
    border: none !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 18px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    color: #6b7280 !important;
    background: transparent !important;
    transition: all 0.2s ease !important;
    margin-bottom: -1px !important;
}
.gradio-container .tab-nav button:hover {
    color: #4f46e5 !important;
    background: rgba(79, 70, 229, 0.05) !important;
}
.gradio-container .tab-nav button.selected {
    color: #4f46e5 !important;
    font-weight: 600 !important;
    background: white !important;
    border: 1px solid #e5e7eb !important;
    border-bottom: 1px solid white !important;
    position: relative !important;
}
.gradio-container .tab-nav button.selected::after {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    height: 2px !important;
    background: linear-gradient(90deg, #4f46e5, #7c3aed) !important;
    border-radius: 8px 8px 0 0 !important;
}

/* ===== 组件通用美化 ===== */
.gradio-container label {
    font-weight: 500 !important;
    color: #374151 !important;
    font-size: 13px !important;
    margin-bottom: 6px !important;
}
.gradio-container input[type="text"],
.gradio-container textarea {
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.gradio-container input[type="text"]:focus,
.gradio-container textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}
.gradio-container select,
.gradio-container .gr-dropdown {
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
}

/* ===== 复选框 ===== */
.gradio-container input[type="checkbox"] {
    accent-color: #4f46e5 !important;
}

/* ===== 文件上传 ===== */
.gradio-container .gr-file,
.gradio-container .upload-container {
    min-height: 200px !important;
    border-radius: 10px !important;
    border: 2px dashed #d1d5db !important;
    transition: all 0.25s ease !important;
}
.gradio-container .gr-file:hover,
.gradio-container .upload-container:hover {
    border-color: #6366f1 !important;
    background: rgba(99, 102, 241, 0.02) !important;
}

/* ===== Tab 内容区 ===== */
.gradio-container .tabitem {
    min-height: 400px !important;
    padding-top: 16px !important;
}

/* ===== 等宽列 ===== */
.equal-width > div {
    flex: 1 !important;
}

/* ===== 输入/输出代码编辑器统一亮色主题 ===== */
.input-code-dark .cm-editor,
.output-code-light .cm-editor {
    background: #ffffff !important;
}

/* ===== 隐藏 Gradio Code 组件原生下载/复制按钮（避免遮挡滚动条）===== */
.code-container .gr-code-download,
.code-container .gr-code-copy,
.code-container [aria-label*="Download"],
.code-container [aria-label*="Copy"],
.code-container [aria-label*="下载"],
.code-container [aria-label*="复制"],
.code-container .cm-editor-header button,
.code-header button.download,
.code-header button.copy {
    display: none !important;
}

/* ===== 下载按钮行 ===== */
.dl-btn-row {
    margin-top: 16px !important;
    gap: 16px !important;
}
.dl-btn-row > div {
    flex: 1 !important;
    max-width: 50% !important;
}

/* ===== 下载按钮美化 ===== */
.dl-download-btn {
    height: 46px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    letter-spacing: 0.01em !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
.dl-download-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px -4px rgba(0,0,0,0.12) !important;
}
.dl-download-btn:active {
    transform: translateY(0) !important;
}
.dl-download-btn:disabled {
    opacity: 0.45 !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

/* ===== 页脚 ===== */
.app-footer {
    text-align: center !important;
    padding: 20px 16px !important;
    color: #9ca3af !important;
    font-size: 12px !important;
    margin-top: 12px !important;
    border-top: 1px solid #e5e7eb !important;
}

/* ===== 响应式微调 ===== */
@media (max-width: 768px) {
    .gradio-container {
        max-width: 100% !important;
        padding: 12px !important;
    }
    .app-header {
        padding: 18px 20px !important;
    }
    .app-header h1 {
        font-size: 20px !important;
    }
}
"""


def _update_file_types(language: str):
    """根据语言切换文件上传组件接受的扩展名"""
    if language == "Java":
        return gr.update(file_types=[".java"])
    return gr.update(file_types=[".py"])


def _download_src(state_src):
    """下载注释后的源码"""
    if state_src:
        return gr.update(value=state_src)
    return gr.update()


def _download_md(state_md):
    """下载 Markdown 文档"""
    if state_md:
        return gr.update(value=state_md)
    return gr.update()


def create_ui():
    """创建并返回 Gradio 界面对象"""
    with gr.Blocks(title="代码注释 Agent") as demo:
        # ===== 顶部导航 =====
        with gr.Column(elem_classes="app-header"):
            gr.Markdown("# 📝 代码注释与 API 文档自动生成 Agent")
            gr.Markdown("粘贴代码或上传文件，AI 自动生成多语言注释和 Markdown API 文档 · 支持 Python & Java")

        # ===== 语言选择 =====
        with gr.Column(elem_classes="card-section"):
            with gr.Row():
                language = gr.Dropdown(
                    choices=["Python", "Java"], value="Python",
                    label="🌐 编程语言", scale=1,
                )
                comment_language = gr.Dropdown(
                    choices=["中文", "English", "日本語"],
                    value="中文",
                    label="🌐 注释语言",
                    scale=1,
                )

        # ===== 输入区 =====
        with gr.Column(elem_classes="card-section"):
            gr.Markdown("### 📥 代码输入")
            with gr.Row():
                with gr.Column(elem_classes="equal-width", scale=1):
                    file_upload = gr.File(
                        label="上传源代码文件",
                        file_types=[".py", ".java"],
                    )
                with gr.Column(elem_classes="equal-width", scale=2):
                    input_box = gr.Code(
                        label="✏️ 代码编辑器",
                        language=None,
                        elem_classes="code-container input-code-dark",
                    )

        # ===== 操作按钮 =====
        with gr.Row():
            btn = gr.Button(
                "🚀 生成注释与文档", variant="primary", size="lg",
                elem_classes="action-btn",
            )
            analyze_btn = gr.Button(
                "🔍 分析代码", variant="secondary", size="lg",
                elem_classes="action-btn",
            )

        # ===== 输出区 =====
        with gr.Column(elem_classes="card-section"):
            with gr.Tabs() as tabs:
                with gr.Tab("📄 带注释的代码", id="annotated_code"):
                    output_code = gr.Code(
                        label="",
                        language=None,
                        elem_classes="code-container output-code-light",
                    )
                    with gr.Row(elem_classes="dl-btn-row"):
                        dl_src_btn = gr.DownloadButton(
                            "📥 下载注释后的代码",
                            elem_classes="dl-download-btn",
                            variant="primary",
                        )
                        dl_md_btn = gr.DownloadButton(
                            "📥 下载 Markdown 文档",
                            elem_classes="dl-download-btn",
                            variant="secondary",
                        )
                    state_src_path = gr.State(None)
                    state_md_path = gr.State(None)

                with gr.Tab("📚 API 文档", id="api_docs"):
                    output_docs = gr.Markdown(elem_classes="scrollable-md")

                with gr.Tab("🔍 代码分析", id="code_analysis"):
                    gr.Markdown("### 📊 代码质量分析")
                    quality_output = gr.Markdown(elem_classes="scrollable-md")
                    gr.Markdown("### 🎯 类型注解检查")
                    annotation_output = gr.Markdown(elem_classes="scrollable-md")
                    gr.Markdown("### 📝 代码摘要")
                    summary_output = gr.Markdown(elem_classes="scrollable-md")
                    analyze_log = gr.Textbox(label="分析日志")

                with gr.Tab("📋 处理日志", id="process_log"):
                    output_log = gr.Textbox(label="处理日志")

        # ===== 页脚 =====
        gr.Markdown(
            "Powered by DeepSeek LLM · Gradio 6.0 · 自动生成中文注释与文档",
            elem_classes="app-footer",
        )

        # ===== 事件绑定 =====
        file_upload.change(fn=handle_file_upload, inputs=file_upload, outputs=[input_box, language])
        language.change(fn=_update_file_types, inputs=language, outputs=file_upload)
        btn.click(
            fn=lambda code, lang, clang: process_code(code, True, lang, clang),
            inputs=[input_box, language, comment_language],
            outputs=[output_code, output_docs, output_log, state_md_path, state_src_path],
        ).then(
            fn=lambda: gr.update(selected="annotated_code"),
            outputs=[tabs],
        )
        dl_src_btn.click(
            fn=_download_src,
            inputs=[state_src_path],
            outputs=[dl_src_btn],
        )
        dl_md_btn.click(
            fn=_download_md,
            inputs=[state_md_path],
            outputs=[dl_md_btn],
        )
        analyze_btn.click(
            fn=analyze_code,
            inputs=[input_box, language, comment_language],
            outputs=[quality_output, annotation_output, summary_output, analyze_log],
        ).then(
            fn=lambda: gr.update(selected="code_analysis"),
            outputs=[tabs],
        )

    return demo