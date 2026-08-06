# -*- coding: utf-8 -*-
"""Gradio 界面模块：构建美观的 Web 交互界面"""
import gradio as gr
from processor import process_code, analyze_code, handle_file_upload, process_batch_files
from i18n import LANGUAGES, t

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
/* 顶部标题行：标题左 + 语言切换右 */
.header-row {
    display: flex !important;
    align-items: flex-start !important;
    justify-content: space-between !important;
    gap: 16px !important;
}
.header-row > div:first-child {
    flex: 1 !important;
    min-width: 0 !important;
}
.header-lang-switcher {
    min-width: 160px !important;
    max-width: 200px !important;
    position: relative !important;
    z-index: 2 !important;
}
.header-lang-switcher label {
    color: rgba(255,255,255,0.9) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    margin-bottom: 4px !important;
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


def _apply_ui_language(lang: str):
    """切换 UI 语言时，返回所有组件的更新列表

    Args:
        lang: 目标语言（"中文" / "English" / "日本語"）

    Returns:
        list: 各组件的 gr.update，顺序与 outputs 列表严格一致
    """
    return [
        gr.update(value=t("app_title", lang)),          # 0  app_title_md
        gr.update(value=t("app_subtitle", lang)),       # 1  app_subtitle_md
        gr.update(label=t("prog_lang_label", lang)),    # 2  language
        gr.update(value=t("input_section", lang)),      # 3  input_section_md
        gr.update(label=t("upload_label", lang)),       # 4  file_upload
        gr.update(label=t("editor_label", lang)),       # 5  input_box
        gr.update(value=t("gen_btn", lang)),            # 6  btn
        gr.update(value=t("analyze_btn", lang)),        # 7  analyze_btn
        gr.update(label=t("tab_annotated", lang)),      # 8  tab_annotated
        gr.update(label=t("output_code_label", lang)), # 9  output_code
        gr.update(label=t("dl_src_btn", lang)),         # 10 dl_src_btn
        gr.update(label=t("dl_md_btn", lang)),          # 11 dl_md_btn
        gr.update(label=t("tab_docs", lang)),           # 12 tab_docs
        gr.update(label=t("tab_analysis", lang)),       # 13 tab_analysis
        gr.update(value=t("quality_title", lang)),      # 14 quality_title_md
        gr.update(value=t("annotation_title", lang)),   # 15 annotation_title_md
        gr.update(value=t("summary_title", lang)),      # 16 summary_title_md
        gr.update(label=t("analyze_log_label", lang)),  # 17 analyze_log
        gr.update(label=t("tab_log", lang)),            # 18 tab_log
        gr.update(label=t("process_log_label", lang)),  # 19 output_log
        gr.update(value=t("footer", lang)),             # 20 footer_md
        # ===== 批量处理新增 =====
        gr.update(value=t("batch_section", lang)),      # 21 batch_section_md
        gr.update(label=t("batch_upload_label", lang)), # 22 batch_file_upload
        gr.update(value=t("batch_gen_btn", lang)),      # 23 batch_gen_btn
        gr.update(label=t("batch_dl_btn", lang)),       # 24 batch_dl_btn
        gr.update(label=t("batch_log_label", lang)),    # 25 batch_log
    ]


def create_ui():
    """创建并返回 Gradio 界面对象"""
    default_lang = "中文"
    with gr.Blocks(title=t("page_title", default_lang)) as demo:
        # ===== 顶部导航（标题左 + 语言切换右）=====
        with gr.Column(elem_classes="app-header"):
            with gr.Row(elem_classes="header-row"):
                with gr.Column():
                    app_title_md = gr.Markdown(t("app_title", default_lang))
                    app_subtitle_md = gr.Markdown(t("app_subtitle", default_lang))
                with gr.Column(elem_classes="header-lang-switcher"):
                    ui_lang = gr.Dropdown(
                        choices=LANGUAGES, value=default_lang,
                        label=t("ui_lang_label", default_lang),
                    )

        # ===== 编程语言选择 =====
        with gr.Column(elem_classes="card-section"):
            language = gr.Dropdown(
                choices=["Python", "Java"], value="Python",
                label=t("prog_lang_label", default_lang),
            )

        # ===== 输入区 =====
        with gr.Column(elem_classes="card-section"):
            input_section_md = gr.Markdown(t("input_section", default_lang))
            with gr.Row():
                with gr.Column(elem_classes="equal-width", scale=1):
                    file_upload = gr.File(
                        label=t("upload_label", default_lang),
                        file_types=[".py", ".java"],
                    )
                with gr.Column(elem_classes="equal-width", scale=2):
                    input_box = gr.Code(
                        label=t("editor_label", default_lang),
                        language=None,
                        elem_classes="code-container input-code-dark",
                    )

        # ===== 操作按钮 =====
        with gr.Row():
            btn = gr.Button(
                t("gen_btn", default_lang), variant="primary", size="lg",
                elem_classes="action-btn",
            )
            analyze_btn = gr.Button(
                t("analyze_btn", default_lang), variant="secondary", size="lg",
                elem_classes="action-btn",
            )

        # ===== 批量处理区（多文件 / ZIP） =====
        with gr.Column(elem_classes="card-section"):
            batch_section_md = gr.Markdown(t("batch_section", default_lang))
            batch_file_upload = gr.File(
                label=t("batch_upload_label", default_lang),
                file_count="multiple",
                file_types=[".py", ".java", ".zip"],
            )
            with gr.Row():
                batch_gen_btn = gr.Button(
                    t("batch_gen_btn", default_lang),
                    variant="primary",
                    size="lg",
                    elem_classes="action-btn",
                )
                batch_dl_btn = gr.DownloadButton(
                    label=t("batch_dl_btn", default_lang),
                    variant="secondary",
                    size="lg",
                    elem_classes="dl-download-btn",
                )
            batch_zip_state = gr.State(None)
            batch_log = gr.Textbox(
                label=t("batch_log_label", default_lang),
                lines=10,
            )

        # ===== 输出区 =====
        with gr.Column(elem_classes="card-section"):
            with gr.Tabs() as tabs:
                tab_annotated = gr.Tab(t("tab_annotated", default_lang), id="annotated_code")
                with tab_annotated:
                    output_code = gr.Code(
                        label=t("output_code_label", default_lang),
                        language=None,
                        elem_classes="code-container output-code-light",
                    )
                    with gr.Row(elem_classes="dl-btn-row"):
                        dl_src_btn = gr.DownloadButton(
                            t("dl_src_btn", default_lang),
                            elem_classes="dl-download-btn",
                            variant="primary",
                        )
                        dl_md_btn = gr.DownloadButton(
                            t("dl_md_btn", default_lang),
                            elem_classes="dl-download-btn",
                            variant="secondary",
                        )
                    state_src_path = gr.State(None)
                    state_md_path = gr.State(None)

                tab_docs = gr.Tab(t("tab_docs", default_lang), id="api_docs")
                with tab_docs:
                    output_docs = gr.Markdown(elem_classes="scrollable-md")

                tab_analysis = gr.Tab(t("tab_analysis", default_lang), id="code_analysis")
                with tab_analysis:
                    quality_title_md = gr.Markdown(t("quality_title", default_lang))
                    quality_output = gr.Markdown(elem_classes="scrollable-md")
                    annotation_title_md = gr.Markdown(t("annotation_title", default_lang))
                    annotation_output = gr.Markdown(elem_classes="scrollable-md")
                    summary_title_md = gr.Markdown(t("summary_title", default_lang))
                    summary_output = gr.Markdown(elem_classes="scrollable-md")
                    analyze_log = gr.Textbox(label=t("analyze_log_label", default_lang))

                tab_log = gr.Tab(t("tab_log", default_lang), id="process_log")
                with tab_log:
                    output_log = gr.Textbox(label=t("process_log_label", default_lang))

        # ===== 页脚 =====
        footer_md = gr.Markdown(
            t("footer", default_lang),
            elem_classes="app-footer",
        )

        # ===== 事件绑定 =====
        file_upload.change(fn=handle_file_upload, inputs=file_upload, outputs=[input_box, language])
        language.change(fn=_update_file_types, inputs=language, outputs=file_upload)

        # UI 语言切换 → 更新所有界面文本（顺序与 _apply_ui_language 返回值严格一致）
        ui_lang.change(
            fn=_apply_ui_language,
            inputs=[ui_lang],
            outputs=[
                app_title_md,       # 0
                app_subtitle_md,    # 1
                language,           # 2
                input_section_md,   # 3
                file_upload,        # 4
                input_box,          # 5
                btn,                # 6
                analyze_btn,        # 7
                tab_annotated,      # 8
                output_code,        # 9
                dl_src_btn,         # 10
                dl_md_btn,          # 11
                tab_docs,           # 12
                tab_analysis,       # 13
                quality_title_md,   # 14
                annotation_title_md,# 15
                summary_title_md,   # 16
                analyze_log,        # 17
                tab_log,            # 18
                output_log,         # 19
                footer_md,          # 20
                # ===== 批量处理新增 =====
                batch_section_md,   # 21
                batch_file_upload,  # 22
                batch_gen_btn,      # 23
                batch_dl_btn,       # 24
                batch_log,          # 25
            ],
        )

        # 生成注释（传入 UI 语言作为注释语言）
        btn.click(
            fn=lambda code, plang, ulang: process_code(code, True, plang, ulang),
            inputs=[input_box, language, ui_lang],
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
        # 分析代码（传入 UI 语言作为摘要语言）
        analyze_btn.click(
            fn=lambda code, plang, ulang: analyze_code(code, plang, ulang),
            inputs=[input_box, language, ui_lang],
            outputs=[quality_output, annotation_output, summary_output, analyze_log],
        ).then(
            fn=lambda: gr.update(selected="code_analysis"),
            outputs=[tabs],
        )

        # ===== 批量处理事件绑定 =====
        def _batch_gen(files, ulang):
            """批量生成包装：返回 (日志, zip_state, zip_download_update)"""
            log, zip_path = process_batch_files(files, comment_lang=ulang, incremental=True)
            dl_update = gr.update(value=zip_path) if zip_path else gr.update()
            return log, zip_path, dl_update

        def _batch_dl(state_zip):
            """下载批量 zip"""
            if state_zip:
                return gr.update(value=state_zip)
            return gr.update()

        batch_gen_btn.click(
            fn=_batch_gen,
            inputs=[batch_file_upload, ui_lang],
            outputs=[batch_log, batch_zip_state, batch_dl_btn],
        )
        batch_dl_btn.click(
            fn=_batch_dl,
            inputs=[batch_zip_state],
            outputs=[batch_dl_btn],
        )

    return demo