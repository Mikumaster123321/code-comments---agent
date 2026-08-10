# -*- coding: utf-8 -*-
"""Gradio 界面模块：构建美观的 Web 交互界面"""
import gradio as gr
from processor import (
    process_code, analyze_code, handle_file_upload,
    process_batch_files, build_split_diff_html,
    process_code_with_progress, process_batch_with_progress,
    CancelToken,
    NAMING_SAME, NAMING_SUFFIX, NAMING_SUBDIR,
    save_workspace, load_workspace, clear_workspace,
)
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

/* ===== v2.3.6 CodeMirror 搜索面板美化（Ctrl+F / Cmd+F 触发）===== */
/* 确保搜索面板容器可见、不被隐藏按钮规则误伤 */
.code-container .cm-panels {
    display: flex !important;
    flex-direction: column !important;
    border-bottom: 1px solid #e5e7eb !important;
    background: #f9fafb !important;
    order: -1 !important;  /* 搜索面板显示在编辑器顶部 */
}
/* 搜索面板输入框 */
.code-container .cm-panels .cm-textfield {
    border: 1px solid #d1d5db !important;
    border-radius: 6px !important;
    padding: 4px 8px !important;
    font-size: 13px !important;
    background: #fff !important;
    color: #1f2937 !important;
    outline: none !important;
}
.code-container .cm-panels .cm-textfield:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
}
/* 搜索面板按钮 */
.code-container .cm-panels .cm-button {
    border: 1px solid #d1d5db !important;
    border-radius: 6px !important;
    padding: 3px 10px !important;
    font-size: 12px !important;
    color: #374151 !important;
    background: #fff !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
}
.code-container .cm-panels .cm-button:hover {
    background: #f3f4f6 !important;
    border-color: #9ca3af !important;
}
/* 搜索匹配高亮 */
.code-container .cm-searchMatch {
    background: rgba(250, 204, 21, 0.4) !important;
    border-radius: 2px !important;
}
.code-container .cm-searchMatch-selected {
    background: rgba(249, 115, 22, 0.5) !important;
    color: #fff !important;
}
/* 搜索面板标签 */
.code-container .cm-panels .cm-panel label {
    font-size: 12px !important;
    color: #6b7280 !important;
}
.code-container .cm-panels .cm-panel .cm-panel-collapser {
    color: #9ca3af !important;
}

/* ===== v2.3.6 大纲折叠 details/summary 美化 ===== */
.outline-sidebar details {
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    margin: 4px 0 !important;
    background: #fff !important;
    overflow: hidden !important;
    transition: border-color 0.15s ease !important;
}
.outline-sidebar details:hover {
    border-color: #c7d2fe !important;
}
.outline-sidebar details[open] {
    border-color: #6366f1 !important;
    box-shadow: 0 1px 4px rgba(99, 102, 241, 0.08) !important;
}
.outline-sidebar summary {
    cursor: pointer !important;
    padding: 8px 12px !important;
    font-size: 14px !important;
    color: #1f2937 !important;
    list-style: none !important;  /* 移除原生三角 */
    user-select: none !important;
    display: flex !important;
    align-items: center !important;
    gap: 4px !important;
    transition: background 0.15s ease !important;
}
.outline-sidebar summary:hover {
    background: #f9fafb !important;
}
/* 自定义折叠箭头 */
.outline-sidebar summary::before {
    content: '▶' !important;
    font-size: 10px !important;
    color: #9ca3af !important;
    transition: transform 0.2s ease !important;
    display: inline-block !important;
    width: 14px !important;
    flex-shrink: 0 !important;
}
.outline-sidebar details[open] > summary::before {
    transform: rotate(90deg) !important;
    color: #6366f1 !important;
}
/* 折叠内嵌子列表 */
.outline-sidebar details > ul {
    margin: 0 !important;
    padding: 4px 0 8px 28px !important;
    list-style: none !important;
}
.outline-sidebar details > ul > li {
    padding: 4px 8px !important;
    font-size: 13px !important;
    border-radius: 4px !important;
    transition: background 0.15s ease !important;
}
.outline-sidebar details > ul > li:hover {
    background: #f3f4f6 !important;
}
/* 大纲内链接样式 */
.outline-sidebar summary a,
.outline-sidebar details > ul > li a {
    color: #4f46e5 !important;
    text-decoration: none !important;
}
.outline-sidebar summary a:hover,
.outline-sidebar details > ul > li a:hover {
    text-decoration: underline !important;
}
.outline-sidebar summary code,
.outline-sidebar details > ul > li code {
    background: #eef2ff !important;
    padding: 1px 5px !important;
    border-radius: 4px !important;
    font-size: 13px !important;
    color: #3730a3 !important;
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
}
.outline-sidebar summary small,
.outline-sidebar details > ul > li small {
    color: #9ca3af !important;
    font-size: 11px !important;
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
        gr.update(label=f'{t("output_code_label", lang)}  ·  {t("search_hint", lang)}'), # 9  output_code
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
        # ===== 注释风格新增 =====
        gr.update(value=t("style_section", lang)),      # 26 style_section_md
        gr.update(label=t("python_style_label", lang)), # 27 python_style
        gr.update(label=t("java_style_label", lang)),   # 28 java_style
        # ===== Diff 视图新增 =====
        gr.update(label=t("tab_diff", lang)),           # 29 tab_diff
        # ===== 函数/类导航大纲新增（占位：outline_md/docs_toc_md 内容在生成时动态填充，切换语言时保留）=====
        gr.update(),  # 30 outline_md
        gr.update(),  # 31 docs_toc_md
        # ===== API Key 预检 / Token 估算新增 =====
        gr.update(value=t("preflight_btn", lang)),  # 32 preflight_btn
        gr.update(label=t("preflight_label", lang)),  # 33 preflight_result_md
        gr.update(label=t("estimate_label", lang)),   # 34 cost_estimate_md
        # ===== v2.3.5 ZIP 输出命名策略新增 =====
        gr.update(value=t("naming_section", lang)),   # 35 naming_section_md
        gr.update(label=t("naming_label", lang)),     # 36 naming_strategy
        # ===== v2.3.7 会话持久化新增 =====
        gr.update(value=t("workspace_title", lang)),    # 37 workspace_title_md
        gr.update(value=t("workspace_save_btn", lang)), # 38 ws_save_btn
        gr.update(value=t("workspace_restore_btn", lang)),# 39 ws_restore_btn
        gr.update(value=t("workspace_clear_btn", lang)),# 40 ws_clear_btn
        gr.update(value=t("workspace_tip", lang)),      # 41 ws_tip_md
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

        # ===== 注释风格选择 =====
        with gr.Column(elem_classes="card-section"):
            style_section_md = gr.Markdown(t("style_section", default_lang))
            with gr.Row():
                with gr.Column(elem_classes="equal-width", scale=1):
                    python_style = gr.Dropdown(
                        choices=["Google 风格", "NumPy 风格", "reStructuredText"],
                        value="Google 风格",
                        label=t("python_style_label", default_lang),
                        allow_custom_value=False,
                    )
                with gr.Column(elem_classes="equal-width", scale=1):
                    java_style = gr.Dropdown(
                        choices=["标准 Javadoc", "极简行内注释"],
                        value="标准 Javadoc",
                        label=t("java_style_label", default_lang),
                        allow_custom_value=False,
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
            cancel_btn = gr.Button(
                t("cancel_btn", default_lang), variant="stop", size="lg",
                elem_classes="action-btn",
            )
            preflight_btn = gr.Button(
                t("preflight_btn", default_lang), variant="secondary", size="lg",
                elem_classes="action-btn",
            )
        # 单文件取消标志位
        state_single_cancel = gr.State(None)
        # ===== API Key 预检 / Token 用量估算 =====
        preflight_result_md = gr.Markdown(
            label=t("preflight_label", default_lang),
            elem_classes="scrollable-md",
        )
        cost_estimate_md = gr.Markdown(
            label=t("estimate_label", default_lang),
            elem_classes="scrollable-md",
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
                batch_cancel_btn = gr.Button(
                    t("batch_cancel_btn", default_lang),
                    variant="stop",
                    size="lg",
                    elem_classes="action-btn",
                )
            # ===== v2.3.5 ZIP 输出命名策略 =====
            naming_section_md = gr.Markdown(t("naming_section", default_lang))
            naming_strategy = gr.Dropdown(
                choices=[
                    (t("naming_suffix_label", default_lang), NAMING_SUFFIX),
                    (t("naming_same_label", default_lang), NAMING_SAME),
                    (t("naming_subdir_label", default_lang), NAMING_SUBDIR),
                ],
                value=NAMING_SUFFIX,
                label=t("naming_label", default_lang),
                allow_custom_value=False,
            )

            # ===== v2.3.7 会话持久化（保存 / 恢复工作区）=====
            workspace_title_md = gr.Markdown(t("workspace_title", default_lang))
            with gr.Row():
                ws_save_btn = gr.Button(
                    t("workspace_save_btn", default_lang),
                    variant="secondary", size="lg",
                )
                ws_restore_btn = gr.Button(
                    t("workspace_restore_btn", default_lang),
                    variant="secondary", size="lg",
                )
                ws_clear_btn = gr.Button(
                    t("workspace_clear_btn", default_lang),
                    variant="secondary", size="lg",
                )
            ws_tip_md = gr.Markdown(t("workspace_tip", default_lang))

            batch_zip_state = gr.State(None)
            batch_log = gr.Textbox(
                label=t("batch_log_label", default_lang),
                lines=10,
            )
            # 批量取消标志位
            state_batch_cancel = gr.State(None)

        # ===== 输出区 =====
        with gr.Column(elem_classes="card-section"):
            with gr.Tabs() as tabs:
                tab_annotated = gr.Tab(t("tab_annotated", default_lang), id="annotated_code")
                with tab_annotated:
                    # 顶部导航大纲（点击大纲链接跳到 tab_docs API 文档对应章节锚点）
                    outline_md = gr.Markdown(elem_classes="scrollable-md outline-sidebar")
                    output_code = gr.Code(
                        label=f'{t("output_code_label", default_lang)}  ·  {t("search_hint", default_lang)}',
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

                tab_diff = gr.Tab(t("tab_diff", default_lang), id="code_diff")
                with tab_diff:
                    diff_html = gr.HTML()

                tab_docs = gr.Tab(t("tab_docs", default_lang), id="api_docs")
                with tab_docs:
                    # Tab 顶部独立目录栏（再次展示大纲，点击本 Tab 内部锚点滚动定位）
                    docs_toc_md = gr.Markdown(elem_classes="scrollable-md docs-toc")
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
                batch_file_upload, # 22
                batch_gen_btn,     # 23
                batch_dl_btn,      # 24
                batch_log,         # 25
                # ===== 注释风格新增 =====
                style_section_md,  # 26
                python_style,      # 27
                java_style,        # 28
                # ===== Diff 视图新增 =====
                tab_diff,          # 29
                # ===== 函数/类导航大纲新增 =====
                outline_md,        # 30
                docs_toc_md,       # 31
                # ===== API Key 预检 / Token 估算新增 =====
                preflight_btn,     # 32
                preflight_result_md,  # 33
                cost_estimate_md,  # 34
                # ===== v2.3.5 ZIP 输出命名策略新增 =====
                naming_section_md,   # 35
                naming_strategy,     # 36
                # ===== v2.3.7 会话持久化新增 =====
                workspace_title_md,    # 37
                ws_save_btn,           # 38
                ws_restore_btn,        # 39
                ws_clear_btn,          # 40
                ws_tip_md,             # 41
            ],
        )

        # ===== 取消任务处理函数 =====
        def _cancel_single(cancel_token):
            if cancel_token is not None and isinstance(cancel_token, CancelToken):
                cancel_token.cancel()
            return None

        def _cancel_batch(cancel_token):
            if cancel_token is not None and isinstance(cancel_token, CancelToken):
                cancel_token.cancel()
            return None

        # 生成注释（生成器版：实时进度 + gr.Progress 进度条 + 支持取消）
        def _gen_with_progress(code, plang, ulang, pyst, jvst, progress=gr.Progress()):
            """单文件注释生成（生成器），每一步 yield 5 元组保持 outputs 结构一致。

            结构：[output_code, output_docs, output_log, state_md_path, state_src_path]
            """
            cancel_token = CancelToken()
            # 第一帧：先返回 cancel_token 给 state（但不影响 UI 渲染）——通过闭包不占 outputs
            # 注：CancelToken 通过 gr.State 在按钮之间共享，这里先记录一个局部变量
            # 我们通过闭包 + 生成器在 yield 前先更新全局 state。为了简单，
            # state_single_cancel 通过 btn.click 的额外 inputs/outputs 绑定（见下）
            pass  # CancelToken 通过 state_single_cancel 单独传递（见 inputs/outputs 绑定）

        # 改为：直接把 CancelToken 放在闭包，通过 cancel_btn 的点击回调操作它
        # 使用一个更稳妥的方案：把 state_single_cancel 作为 btn.click 的额外 output
        # 在第一次 yield 时返回新的 CancelToken，后续每次 yield None（保持最新 token）
        def _gen_real(code, plang, ulang, pyst, jvst, cancel_token_state, progress=gr.Progress()):
            """真实的生成器：创建 CancelToken，逐帧 yield。

            outputs 结构（11 元组）：
              [output_code, output_docs, output_log, state_md_path, state_src_path,
               state_single_cancel, diff_html, outline_md, docs_toc_md,
               preflight_result_md, cost_estimate_md]
            中间态除了 output_log / state_single_cancel 之外，其余可保持 None（Gradio 保留上一帧）。
            """
            import processor as _p_mod
            # —— 第一帧前：API Key 预检 + 用量估算（不阻塞，6s 超时），失败直接返回不进入生成主流程
            try:
                ok, pf_md, est_md = _p_mod.preflight_check(
                    source_code=code or "", language=plang, ui_lang=ulang, do_ping=True,
                )
            except Exception as _pf_err:
                ok, pf_md, est_md = False, f"**❌ 预检异常（Preflight Exception）**\n\n> {type(_pf_err).__name__}: {_pf_err}", ""
            # 失败：只输出错误（不生成，保留现有 outputs 不变 → 首 7 位 None + 大纲 + 预检 + 估算）
            if not ok:
                # 失败时照样给大纲和估算，让用户能看到（预检失败不代表 AST 解析失败）
                try:
                    _title = t("outline_title", ulang) if ulang else "📋 函数/类导航大纲"
                    early_outline = _p_mod.build_outline_markdown(code or "", plang, title=_title)
                except Exception:
                    early_outline = ""
                yield None, None, None, None, None, None, None, early_outline, early_outline, pf_md, est_md
                return  # 预检失败 → 提前 return，不再触发生成（避免跑到一半 Key 无效白跑）

            # 创建新的 CancelToken（先重置）
            token = CancelToken()
            # progress_cb 绑定到 Gradio 的 progress 对象
            def _cb(ratio, desc):
                progress(ratio, desc=desc)
            # 用于最后拿到 annotated_code 给 Diff
            last_annotated = None
            last_final_frame = None
            # 先在第 0 帧（第一帧）就把大纲渲染出来，用户一开始就能看到函数/类列表
            try:
                import processor as _p
                _title = t("outline_title", ulang) if ulang else "📋 函数/类导航大纲"
                early_outline = _p.build_outline_markdown(code or "", plang, title=_title)
            except Exception:
                early_outline = ""
            # 透传 processor 的生成器，11 元组 outputs（末 2 位是 preflight_md + estimate_md）
            first = True
            for frame in process_code_with_progress(
                code, incremental=True, language=plang, comment_lang=ulang,
                python_style=pyst, java_style=jvst,
                cancel_token=token, progress_cb=_cb,
            ):
                ann, md, log_txt, md_p, src_p = frame
                if first:
                    first = False
                    # 第 1 帧：把 cancel_token 存入 state，大纲先渲染（第 8、9 位）；预检/估算也先填入
                    yield ann, md, log_txt, md_p, src_p, token, None, early_outline, early_outline, pf_md, est_md
                    continue
                if ann is not None and md_p is not None and src_p is not None:
                    last_final_frame = frame
                    last_annotated = ann
                # 中间帧：大纲/预检/估算保持不变（None 继承上一帧不闪烁）
                yield ann, md, log_txt, md_p, src_p, None, None, None, None, None, None
            # 最后：构建 Diff HTML + 最终大纲（再次渲染，语言用最终 comment_lang）+ 最终估算（再算一遍保持一致）
            try:
                _ok2, pf_md_f, est_md_f = _p_mod.preflight_check(
                    source_code=code or "", language=plang, ui_lang=ulang, do_ping=False,
                )
                pf_md_final = pf_md_f if pf_md_f else pf_md
                est_md_final = est_md_f if est_md_f else est_md
            except Exception:
                pf_md_final, est_md_final = pf_md, est_md
            if last_final_frame is not None:
                ann_code = last_final_frame[0]
                diff = build_split_diff_html(code, ann_code, plang)
                try:
                    _title = t("outline_title", ulang) if ulang else "📋 函数/类导航大纲"
                    final_outline = _p.build_outline_markdown(code or "", plang, title=_title)
                except Exception:
                    final_outline = ""
                ann, md, log_txt, md_p, src_p = last_final_frame
                yield ann, md, log_txt, md_p, src_p, None, diff, final_outline, final_outline, pf_md_final, est_md_final
            else:
                # 没产生最终帧（例：空输入 / 取消），把大纲保留之前的 early_outline，估算保持不变
                yield None, None, None, None, None, None, None, early_outline, early_outline, pf_md_final, est_md_final

        # ===== 仅估算（不发网络请求）：输入/语言/风格变化时实时刷新 cost_estimate_md =====
        def _estimate_only(code, plang, ulang, pyst, jvst):
            try:
                import processor as _pp
                _, _, est = _pp.preflight_check(
                    source_code=code or "", language=plang, ui_lang=ulang, do_ping=False,
                )
                return est
            except Exception as e:
                return f"> 估算失败（Estimate Error）：{type(e).__name__}: {e}"

        # ===== 手动预检按钮：主动发 1-token 心跳 =====
        def _preflight_manual(code, plang, ulang, pyst, jvst):
            try:
                import processor as _pp
                ok, pf, est = _pp.preflight_check(
                    source_code=code or "", language=plang, ui_lang=ulang, do_ping=True,
                )
                return pf, est
            except Exception as e:
                return (
                    f"**❌ 预检异常（Preflight Exception）**\n\n> {type(e).__name__}: {e}",
                    _estimate_only(code, plang, ulang, pyst, jvst),
                )

        # 把 btn.click 改成调用生成器（outputs 11 个：末 2 位 preflight_result_md / cost_estimate_md）
        btn.click(
            fn=_gen_real,
            inputs=[input_box, language, ui_lang, python_style, java_style, state_single_cancel],
            outputs=[output_code, output_docs, output_log, state_md_path, state_src_path,
                     state_single_cancel, diff_html, outline_md, docs_toc_md,
                     preflight_result_md, cost_estimate_md],
        ).then(
            fn=lambda: gr.update(selected="annotated_code"),
            outputs=[tabs],
        )
        # 手动预检按钮绑定
        preflight_btn.click(
            fn=_preflight_manual,
            inputs=[input_box, language, ui_lang, python_style, java_style],
            outputs=[preflight_result_md, cost_estimate_md],
        )
        # 输入/语言/风格变化 → 自动刷新成本估算（不发网络请求）
        for _src in (input_box, language, ui_lang, python_style, java_style, file_upload):
            try:
                _src.change(
                    fn=_estimate_only,
                    inputs=[input_box, language, ui_lang, python_style, java_style],
                    outputs=[cost_estimate_md],
                )
            except Exception:
                # 某些组件可能没有 .change 方法（安全跳过）
                pass
        # 取消按钮：只调用 cancel，不需要返回值
        cancel_btn.click(
            fn=_cancel_single,
            inputs=[state_single_cancel],
            outputs=[],
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

        # ===== 批量处理事件绑定（生成器版） =====
        def _batch_gen_progress(files, ulang, pyst, jvst, naming, cancel_token_state, progress=gr.Progress()):
            """批量生成（生成器），outputs 结构：
            [batch_log, batch_zip_state, batch_dl_btn, state_batch_cancel]

            v2.3.5 新增 naming 参数：ZIP 源码输出命名策略 same / suffix / subdir。
            """
            token = CancelToken()
            def _cb(ratio, desc):
                progress(ratio, desc=desc)
            first = True
            for log_text, zip_path in process_batch_with_progress(
                files, comment_lang=ulang, incremental=True,
                python_style=pyst, java_style=jvst,
                naming_strategy=naming,
                cancel_token=token, progress_cb=_cb,
            ):
                if first:
                    first = False
                    dl_upd = gr.update() if not zip_path else gr.update(value=zip_path)
                    yield log_text, zip_path, dl_upd, token
                    continue
                dl_upd = gr.update(value=zip_path) if zip_path else gr.update()
                yield log_text, zip_path, dl_upd, None

        def _batch_dl(state_zip):
            """下载批量 zip"""
            if state_zip:
                return gr.update(value=state_zip)
            return gr.update()

        batch_gen_btn.click(
            fn=_batch_gen_progress,
            inputs=[batch_file_upload, ui_lang, python_style, java_style, naming_strategy, state_batch_cancel],
            outputs=[batch_log, batch_zip_state, batch_dl_btn, state_batch_cancel],
        )
        batch_cancel_btn.click(
            fn=_cancel_batch,
            inputs=[state_batch_cancel],
            outputs=[],
        )
        batch_dl_btn.click(
            fn=_batch_dl,
            inputs=[batch_zip_state],
            outputs=[batch_dl_btn],
        )

        # ===== v2.3.7 会话持久化：保存 / 恢复 / 清除 =====
        def _ws_save(src, lang, ulang, pyst, jvst, naming):
            data = {
                "source_code": src,
                "language": lang,
                "ui_lang": ulang,
                "python_style": pyst,
                "java_style": jvst,
                "naming_strategy": naming,
            }
            ok, msg = save_workspace(data)
            return (
                gr.update(
                    value=f"\n{msg}\n",
                ),
            )

        def _ws_restore():
            ok, msg, data = load_workspace()
            return (
                data.get("source_code", ""),
                data.get("language", "Python"),
                data.get("ui_lang", "中文"),
                data.get("python_style", "默认"),
                data.get("java_style", "默认"),
                data.get("naming_strategy", NAMING_SUFFIX),
                f"\n{msg}\n",
            )

        def _ws_clear():
            ok, msg = clear_workspace()
            return (
                gr.update(value=f"\n{msg}\n"),
            )

        ws_save_btn.click(
            fn=_ws_save,
            inputs=[input_box, language, ui_lang, python_style, java_style, naming_strategy],
            outputs=[output_log],
        )
        ws_restore_btn.click(
            fn=_ws_restore,
            inputs=[],
            outputs=[input_box, language, ui_lang, python_style, java_style, naming_strategy, output_log],
        )
        ws_clear_btn.click(
            fn=_ws_clear,
            inputs=[],
            outputs=[output_log],
        )

    return demo