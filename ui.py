# -*- coding: utf-8 -*-
"""Gradio 界面模块：构建美观的 Web 交互界面
v2.4.1 小更新：macOS + 手机端响应式自适应
"""
import gradio as gr
from processor import (
    process_code, analyze_code, handle_file_upload,
    process_batch_files, build_split_diff_html,
    process_code_with_progress, process_batch_with_progress,
    CancelToken,
    NAMING_SAME, NAMING_SUFFIX, NAMING_SUBDIR,
    save_workspace, load_workspace, clear_workspace,
)
from i18n import LANGUAGES, t, user_error_message
import config as _cfg

from code_comments_agent.ui_styles import CUSTOM_CSS


def _update_file_types(language: str):
    """根据语言切换文件上传组件接受的扩展名"""
    if language == "Java":
        return gr.update(file_types=[".java"])
    return gr.update(file_types=[".py"])


def _update_style_controls(language: str):
    """Show only the style selector relevant to the programming language."""
    is_java = language == "Java"
    return gr.update(visible=not is_java), gr.update(visible=is_java)


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


def _python_style_choices(lang: str):
    labels = {
        "中文": ("Google 风格", "NumPy 风格", "reStructuredText"),
        "English": ("Google style", "NumPy style", "reStructuredText"),
        "日本語": ("Google スタイル", "NumPy スタイル", "reStructuredText"),
    }.get(lang, ("Google 风格", "NumPy 风格", "reStructuredText"))
    values = ("Google 风格", "NumPy 风格", "reStructuredText")
    return list(zip(labels, values))


def _java_style_choices(lang: str):
    labels = {
        "中文": ("标准 Javadoc", "简短 Javadoc（原极简模式）"),
        "English": ("Standard Javadoc", "Short Javadoc (minimal mode)"),
        "日本語": ("標準 Javadoc", "短い Javadoc（最小モード）"),
    }.get(lang, ("标准 Javadoc", "简短 Javadoc（原极简模式）"))
    values = ("标准 Javadoc", "极简行内注释")
    return list(zip(labels, values))


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
        # v2.3.8 代码风格检查标题（插在 annotation 和 summary 之间）
        gr.update(value=t("style_title", lang)),        # 16 style_title_md
        gr.update(value=t("summary_title", lang)),      # 17 summary_title_md
        gr.update(label=t("analyze_log_label", lang)),  # 18 analyze_log
        gr.update(label=t("tab_log", lang)),            # 19 tab_log
        gr.update(label=t("process_log_label", lang)),  # 20 output_log
        gr.update(value=t("footer", lang)),             # 21 footer_md
        # ===== 批量处理新增 =====
        gr.update(value=t("batch_section", lang)),      # 22 batch_section_md
        gr.update(label=t("batch_upload_label", lang)), # 23 batch_file_upload
        gr.update(value=t("batch_gen_btn", lang)),      # 24 batch_gen_btn
        gr.update(label=t("batch_dl_btn", lang)),       # 25 batch_dl_btn
        gr.update(label=t("batch_log_label", lang)),    # 26 batch_log
        # ===== 注释风格新增 =====
        gr.update(value=t("style_section", lang)),      # 27 style_section_md
        gr.update(label=t("python_style_label", lang), choices=_python_style_choices(lang)), # 28 python_style
        gr.update(label=t("java_style_label", lang), choices=_java_style_choices(lang)),   # 29 java_style
        # ===== Diff 视图新增 =====
        gr.update(label=t("tab_diff", lang)),           # 30 tab_diff
        # ===== 函数/类导航大纲新增（占位：outline_md/docs_toc_md 内容在生成时动态填充，切换语言时保留）=====
        gr.update(),  # 31 outline_md
        gr.update(),  # 32 docs_toc_md
        # ===== API Key 预检 / Token 估算新增 =====
        gr.update(value=t("preflight_btn", lang)),  # 33 preflight_btn
        gr.update(label=t("preflight_label", lang)),  # 34 preflight_result_md
        gr.update(label=t("estimate_label", lang)),   # 35 cost_estimate_md
        # ===== v2.3.5 ZIP 输出命名策略新增 =====
        gr.update(value=t("naming_section", lang)),   # 36 naming_section_md
        gr.update(label=t("naming_label", lang)),     # 37 naming_strategy
        # ===== v2.3.7 会话持久化新增 =====
        gr.update(value=t("workspace_title", lang)),    # 38 workspace_title_md
        gr.update(value=t("workspace_save_btn", lang)), # 39 ws_save_btn
        gr.update(value=t("workspace_restore_btn", lang)),# 40 ws_restore_btn
        gr.update(value=t("workspace_clear_btn", lang)),# 41 ws_clear_btn
        gr.update(value=t("workspace_tip", lang)),      # 42 ws_tip_md
        # ===== v2.4.0 多 Provider / 多模型切换新增 =====
        gr.update(value=t("provider_section", lang)),      # 43 provider_section_md
        gr.update(label=t("provider_label", lang)),        # 44 provider_dd
        gr.update(label=t("model_label", lang)),           # 45 model_dd
        gr.update(label=t("api_key_label", lang), placeholder=t("api_key_placeholder", lang)),  # 46 api_key_tb
        gr.update(label=t("base_url_label", lang), placeholder=t("base_url_placeholder", lang)),# 47 base_url_tb
        gr.update(label=t("custom_model_label", lang)),    # 48 custom_model_tb
        gr.update(value=t("apply_provider_btn", lang)),    # 49 apply_provider_btn
        # provider_status_md / provider_info_md 内容是动态的，语言切换时保持 gr.update() 占位
        gr.update(),  # 50 provider_status_md
        gr.update(),  # 51 provider_info_md
        # V3.1.2: label-only updates preserve the independent output language value.
        gr.update(label=t("output_lang_label", lang), info=t("output_lang_help", lang)),  # 52 output_lang
        gr.update(label=t("rewrite_existing_label", lang)),  # 53 rewrite_existing
        gr.update(label=t("provider_advanced_label", lang)),  # 54 provider_advanced
        gr.update(value=t("provider_setup_help", lang)),  # 55 provider_help_md
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
                    output_lang = gr.Dropdown(
                        choices=LANGUAGES, value=default_lang,
                        label="🗣️ Output Language / 输出语言 / 出力言語",
                        info=t("output_lang_help", default_lang),
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
                with gr.Column(elem_classes="equal-width", scale=1, visible=True) as python_style_column:
                    python_style = gr.Dropdown(
                        choices=_python_style_choices(default_lang),
                        value="Google 风格",
                        label=t("python_style_label", default_lang),
                        allow_custom_value=False,
                    )
                with gr.Column(elem_classes="equal-width", scale=1, visible=False) as java_style_column:
                    java_style = gr.Dropdown(
                        choices=_java_style_choices(default_lang),
                        value="标准 Javadoc",
                        label=t("java_style_label", default_lang),
                        allow_custom_value=False,
                    )
            rewrite_existing = gr.Checkbox(
                value=True,
                label="Rewrite existing comments to selected style / 既有注释风格改写 / 既存コメント書換",
                info="Off = translation only; on = translation plus style rewrite.",
            )

        # ===== v2.4.0 Provider / 模型切换区 =====
        with gr.Accordion(
            t("provider_advanced_label", default_lang), open=False,
            elem_classes="card-section",
        ) as provider_advanced:
            provider_section_md = gr.Markdown(t("provider_section", default_lang))
            provider_help_md = gr.Markdown(t("provider_setup_help", default_lang))
            with gr.Row():
                # Provider 下拉框
                provider_dd = gr.Dropdown(
                    choices=_cfg.get_providers(default_lang),
                    value=_cfg.get_active_provider(),
                    label=t("provider_label", default_lang),
                    allow_custom_value=False,
                    scale=1,
                )
                # Model 下拉框（根据当前 Provider 动态刷新）
                model_dd = gr.Dropdown(
                    choices=_cfg.get_models_for_provider(_cfg.get_active_provider(), default_lang),
                    value=_cfg.get_active_model(),
                    label=t("model_label", default_lang),
                    allow_custom_value=True,
                    scale=1,
                )
            with gr.Row():
                # API Key 输入（运行时覆盖，不保存）
                api_key_tb = gr.Textbox(
                    label=t("api_key_label", default_lang),
                    placeholder=t("api_key_placeholder", default_lang),
                    type="password",
                    lines=1,
                    scale=1,
                )
                # Base URL（仅 Azure / Custom 可编辑）
                base_url_tb = gr.Textbox(
                    label=t("base_url_label", default_lang),
                    placeholder=t("base_url_placeholder", default_lang),
                    value=_cfg.get_active_base_url(),
                    lines=1,
                    scale=1,
                    interactive=_cfg.is_active_provider_customizable(),
                )
            # Custom Provider 自定义模型名
            custom_model_tb = gr.Textbox(
                label=t("custom_model_label", default_lang),
                placeholder="例如：qwen2.5-72b-instruct 或 my-local-model",
                lines=1,
                interactive=(_cfg.get_active_provider() == "custom"),
            )
            with gr.Row():
                apply_provider_btn = gr.Button(
                    t("apply_provider_btn", default_lang),
                    variant="primary",
                    size="lg",
                    elem_classes="action-btn",
                )
            # 状态 / 当前信息显示
            provider_status_md = gr.Markdown(
                value=f"{t('provider_settings_applied', default_lang)} · {t('provider_connectivity_not_verified', default_lang)}",
                elem_classes="scrollable-md",
            )
            provider_info_md = gr.Markdown(
                value=t("current_provider_info", default_lang).format(
                    p=_cfg.get_active_provider(),
                    m=_cfg.get_active_model(),
                    u=_cfg.get_active_base_url(),
                ),
                elem_classes="scrollable-md",
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
                elem_classes="action-btn", interactive=False,
            )
            preflight_btn = gr.Button(
                t("preflight_btn", default_lang), variant="secondary", size="lg",
                elem_classes="action-btn",
            )
        # 单文件取消标志位
        state_single_cancel = gr.State(None)
        run_status_md = gr.Markdown(t("status_idle", default_lang))
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
                    elem_classes="action-btn", interactive=False,
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
                    outline_md = gr.Markdown(value=t("empty_output", default_lang), elem_classes="scrollable-md outline-sidebar")
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
                    diff_html = gr.HTML(value=build_split_diff_html("", "", "Python", default_lang))

                tab_docs = gr.Tab(t("tab_docs", default_lang), id="api_docs")
                with tab_docs:
                    # Tab 顶部独立目录栏（再次展示大纲，点击本 Tab 内部锚点滚动定位）
                    docs_toc_md = gr.Markdown(value=t("empty_output", default_lang), elem_classes="scrollable-md docs-toc")
                    output_docs = gr.Markdown(value=t("empty_output", default_lang), elem_classes="scrollable-md")

                tab_analysis = gr.Tab(t("tab_analysis", default_lang), id="code_analysis")
                with tab_analysis:
                    quality_title_md = gr.Markdown(t("quality_title", default_lang))
                    quality_output = gr.Markdown(value=t("empty_output", default_lang), elem_classes="scrollable-md")
                    annotation_title_md = gr.Markdown(t("annotation_title", default_lang))
                    annotation_output = gr.Markdown(value=t("empty_output", default_lang), elem_classes="scrollable-md")
                    # v2.3.8 代码风格检查区块
                    style_title_md = gr.Markdown(t("style_title", default_lang))
                    style_output = gr.Markdown(value=t("empty_output", default_lang), elem_classes="scrollable-md")
                    summary_title_md = gr.Markdown(t("summary_title", default_lang))
                    summary_output = gr.Markdown(value=t("empty_output", default_lang), elem_classes="scrollable-md")
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
        language.change(
            fn=_update_style_controls,
            inputs=language,
            outputs=[python_style_column, java_style_column],
        )

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
                # v2.3.8 代码风格检查标题
                style_title_md,     # 16
                summary_title_md,   # 17
                analyze_log,        # 18
                tab_log,            # 19
                output_log,         # 20
                footer_md,          # 21
                # ===== 批量处理新增 =====
                batch_section_md,   # 22
                batch_file_upload, # 23
                batch_gen_btn,     # 24
                batch_dl_btn,      # 25
                batch_log,         # 26
                # ===== 注释风格新增 =====
                style_section_md,  # 27
                python_style,      # 28
                java_style,        # 29
                # ===== Diff 视图新增 =====
                tab_diff,          # 30
                # ===== 函数/类导航大纲新增 =====
                outline_md,        # 31
                docs_toc_md,       # 32
                # ===== API Key 预检 / Token 估算新增 =====
                preflight_btn,     # 33
                preflight_result_md,  # 34
                cost_estimate_md,  # 35
                # ===== v2.3.5 ZIP 输出命名策略新增 =====
                naming_section_md,   # 36
                naming_strategy,     # 37
                # ===== v2.3.7 会话持久化新增 =====
                workspace_title_md,    # 38
                ws_save_btn,           # 39
                ws_restore_btn,        # 40
                ws_clear_btn,          # 41
                ws_tip_md,             # 42
                # ===== v2.4.0 多 Provider / 多模型切换新增 =====
                provider_section_md,   # 43
                provider_dd,           # 44
                model_dd,              # 45
                api_key_tb,            # 46
                base_url_tb,           # 47
                custom_model_tb,       # 48
                apply_provider_btn,    # 49
                provider_status_md,    # 50
                provider_info_md,      # 51
                output_lang,           # 52 (label/info only; value remains independent)
                rewrite_existing,      # 53
                provider_advanced,     # 54
                provider_help_md,      # 55
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
        def _gen_real(
            code, plang, ui_language, output_language, pyst, jvst,
            rewrite_style, cancel_token_state, progress=gr.Progress(),
        ):
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
                    source_code=code or "", language=plang, ui_lang=ui_language, do_ping=True,
                )
            except Exception:
                ok = False
                pf_md = user_error_message("PROVIDER_FAILURE", ui_language)
                est_md = ""
            # 当前运行失败时清理旧输出，避免旧成功结果被误认成本轮结果。
            if not ok:
                empty = t("empty_output", ui_language)
                yield (
                    "", empty, pf_md, None, None, None,
                    build_split_diff_html("", "", plang, ui_language), empty, empty,
                    pf_md, est_md, t("status_failure", ui_language), gr.update(interactive=False),
                )
                return

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
                _title = t("outline_title", output_language) if output_language else "📋 函数/类导航大纲"
                early_outline = _p.build_outline_markdown(code or "", plang, title=_title)
            except Exception:
                early_outline = ""
            # 透传 processor 的生成器，11 元组 outputs（末 2 位是 preflight_md + estimate_md）
            first = True
            for frame in process_code_with_progress(
                code, incremental=True, language=plang, comment_lang=output_language,
                python_style=pyst, java_style=jvst,
                cancel_token=token, progress_cb=_cb,
                rewrite_existing=rewrite_style,
            ):
                ann, md, log_txt, md_p, src_p = frame
                if first:
                    first = False
                    if ann is not None and md_p is not None and src_p is not None:
                        last_final_frame = frame
                        last_annotated = ann
                    # 第 1 帧：把 cancel_token 存入 state，大纲先渲染（第 8、9 位）；预检/估算也先填入
                    yield ann, md, log_txt, md_p, src_p, token, None, early_outline, early_outline, pf_md, est_md, t("status_running", ui_language), gr.update(interactive=True)
                    continue
                if ann is not None and md_p is not None and src_p is not None:
                    last_final_frame = frame
                    last_annotated = ann
                # 中间帧：大纲/预检/估算保持不变（None 继承上一帧不闪烁）
                yield ann, md, log_txt, md_p, src_p, None, None, None, None, None, None, None, None
            # 最后：构建 Diff HTML + 最终大纲（再次渲染，语言用最终 comment_lang）+ 最终估算（再算一遍保持一致）
            try:
                _ok2, pf_md_f, est_md_f = _p_mod.preflight_check(
                    source_code=code or "", language=plang, ui_lang=ui_language, do_ping=False,
                )
                pf_md_final = pf_md_f if pf_md_f else pf_md
                est_md_final = est_md_f if est_md_f else est_md
            except Exception:
                pf_md_final, est_md_final = pf_md, est_md
            if last_final_frame is not None:
                ann_code = last_final_frame[0]
                diff = build_split_diff_html(code, ann_code, plang, output_language)
                try:
                    _title = t("outline_title", output_language) if output_language else "📋 函数/类导航大纲"
                    final_outline = _p.build_outline_markdown(code or "", plang, title=_title)
                except Exception:
                    final_outline = ""
                ann, md, log_txt, md_p, src_p = last_final_frame
                final_status = t("status_idle", ui_language) if token.is_canceled() else t("status_success", ui_language)
                yield ann, md, log_txt, md_p, src_p, None, diff, final_outline, final_outline, pf_md_final, est_md_final, final_status, gr.update(interactive=False)
            else:
                empty = t("empty_output", ui_language)
                yield "", empty, "", None, None, None, build_split_diff_html("", "", plang, ui_language), empty, empty, pf_md_final, est_md_final, t("status_failure", ui_language), gr.update(interactive=False)

        # ===== 仅估算（不发网络请求）：输入/语言/风格变化时实时刷新 cost_estimate_md =====
        def _estimate_only(code, plang, ui_language, pyst, jvst):
            try:
                import processor as _pp
                _, _, est = _pp.preflight_check(
                    source_code=code or "", language=plang, ui_lang=ui_language, do_ping=False,
                )
                return est
            except Exception:
                return user_error_message("PROVIDER_FAILURE", ui_language)

        # ===== 手动预检按钮：主动发 1-token 心跳 =====
        def _preflight_manual(code, plang, ui_language, pyst, jvst):
            try:
                import processor as _pp
                ok, pf, est = _pp.preflight_check(
                    source_code=code or "", language=plang, ui_lang=ui_language, do_ping=True,
                )
                return pf, est
            except Exception:
                return (
                    user_error_message("PROVIDER_FAILURE", ui_language),
                    _estimate_only(code, plang, ui_language, pyst, jvst),
                )

        # 把 btn.click 改成调用生成器（outputs 11 个：末 2 位 preflight_result_md / cost_estimate_md）
        btn.click(
            fn=_gen_real,
            inputs=[input_box, language, ui_lang, output_lang, python_style, java_style, rewrite_existing, state_single_cancel],
            outputs=[output_code, output_docs, output_log, state_md_path, state_src_path,
                     state_single_cancel, diff_html, outline_md, docs_toc_md,
                     preflight_result_md, cost_estimate_md, run_status_md, cancel_btn],
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
        # 分析与文档展示使用独立 Output Language。
        analyze_btn.click(
            fn=lambda code, plang, output_language: analyze_code(code, plang, output_language),
            inputs=[input_box, language, output_lang],
            outputs=[quality_output, annotation_output, summary_output, style_output, analyze_log],
        ).then(
            fn=lambda: gr.update(selected="code_analysis"),
            outputs=[tabs],
        )

        # ===== 批量处理事件绑定（生成器版） =====
        def _batch_gen_progress(files, output_language, pyst, jvst, rewrite_style, naming, cancel_token_state, progress=gr.Progress()):
            """批量生成（生成器），outputs 结构：
            [batch_log, batch_zip_state, batch_dl_btn, state_batch_cancel]

            v2.3.5 新增 naming 参数：ZIP 源码输出命名策略 same / suffix / subdir。
            """
            token = CancelToken()
            def _cb(ratio, desc):
                progress(ratio, desc=desc)
            first = True
            for log_text, zip_path in process_batch_with_progress(
                files, comment_lang=output_language, incremental=True,
                python_style=pyst, java_style=jvst,
                rewrite_existing=rewrite_style,
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
            inputs=[batch_file_upload, output_lang, python_style, java_style, rewrite_existing, naming_strategy, state_batch_cancel],
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
        def _ws_save(src, lang, ulang, output_language, pyst, jvst, rewrite_style, naming):
            data = {
                "source_code": src,
                "language": lang,
                "ui_lang": ulang,
                "output_lang": output_language,
                "python_style": pyst,
                "java_style": jvst,
                "rewrite_existing": rewrite_style,
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
                data.get("output_lang", data.get("ui_lang", "中文")),
                data.get("python_style", "默认"),
                data.get("java_style", "默认"),
                data.get("rewrite_existing", True),
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
            inputs=[input_box, language, ui_lang, output_lang, python_style, java_style, rewrite_existing, naming_strategy],
            outputs=[output_log],
        )
        ws_restore_btn.click(
            fn=_ws_restore,
            inputs=[],
            outputs=[input_box, language, ui_lang, output_lang, python_style, java_style, rewrite_existing, naming_strategy, output_log],
        )
        ws_clear_btn.click(
            fn=_ws_clear,
            inputs=[],
            outputs=[output_log],
        )

        # ===== v2.4.0 Provider / 模型切换事件绑定 =====
        def _on_provider_change(pkey: str, ulang: str):
            """切换 Provider 下拉框：刷新 Model 列表 + 解锁/锁定 Base URL 和自定义模型名

            Args:
                pkey: 新的 Provider key
                ulang: 当前 UI 语言

            Returns:
                (model_choices_update, base_url_interactive, base_url_value,
                 custom_model_interactive, info_md_update)
            """
            models = _cfg.get_models_for_provider(pkey, ulang)
            first_model = models[0][1] if models else ""
            customizable = _cfg.PROVIDERS[pkey]["customizable_base_url"]
            default_base = _cfg.PROVIDERS[pkey]["base_url"]
            is_custom = (pkey == "custom")
            info = t("current_provider_info", ulang).format(
                p=pkey,
                m=first_model,
                u=default_base,
            )
            return (
                gr.update(choices=models, value=first_model),  # model_dd
                gr.update(interactive=customizable, value=default_base),  # base_url_tb
                gr.update(interactive=is_custom),  # custom_model_tb
                gr.update(value=f"\n{info}\n"),    # provider_info_md
            )

        provider_dd.change(
            fn=_on_provider_change,
            inputs=[provider_dd, ui_lang],
            outputs=[model_dd, base_url_tb, custom_model_tb, provider_info_md],
        )

        def _apply_provider_settings(
            pkey: str, mkey: str, api_key: str, base_url: str,
            custom_model: str, ulang: str,
        ):
            """点击"应用设置"按钮：调用 config.switch_provider 切换 Provider / Model

            Returns:
                (status_md, info_md, base_url_tb_update, custom_model_tb_update, model_dd_update)
            """
            ok, msg = _cfg.switch_provider(
                provider_key=pkey,
                model_key=mkey,
                api_key=api_key if api_key else None,
                base_url=base_url if base_url else None,
                custom_model_name=custom_model if custom_model else None,
            )
            if ok:
                status = (
                    f"{t('provider_settings_applied', ulang)} · "
                    f"{t('provider_connectivity_not_verified', ulang)}"
                )
            else:
                status = user_error_message("PROVIDER_FAILURE", ulang)
            cur_p = _cfg.get_active_provider()
            cur_m = _cfg.get_active_model()
            cur_u = _cfg.get_active_base_url()
            info = t("current_provider_info", ulang).format(p=cur_p, m=cur_m, u=cur_u)
            # 同步 model_dd 的 value（如果 custom provider 下用了自定义模型名）
            new_models = _cfg.get_models_for_provider(cur_p, ulang)
            customizable = _cfg.PROVIDERS[cur_p]["customizable_base_url"]
            is_custom = (cur_p == "custom")
            return (
                gr.update(value=f"\n{status}\n"),                  # provider_status_md
                gr.update(value=f"\n{info}\n"),                    # provider_info_md
                gr.update(value=cur_u, interactive=customizable),  # base_url_tb
                gr.update(interactive=is_custom),                  # custom_model_tb
                gr.update(choices=new_models, value=cur_m),        # model_dd
            )

        apply_provider_btn.click(
            fn=_apply_provider_settings,
            inputs=[provider_dd, model_dd, api_key_tb, base_url_tb, custom_model_tb, ui_lang],
            outputs=[provider_status_md, provider_info_md, base_url_tb, custom_model_tb, model_dd],
        )

    return demo
