# -*- coding: utf-8 -*-
"""国际化模块：UI 文本多语言支持（中文 / English / 日本語）"""

# 支持的 UI 语言
LANGUAGES = ["中文", "English", "日本語"]

# 语言代码映射（用于 LLM 提示词）
LANG_CODE = {
    "中文": "zh",
    "English": "en",
    "日本語": "ja",
}

# 语言英文名（用于 LLM 提示词）
LANG_NAME = {
    "中文": "Chinese (Simplified)",
    "English": "English",
    "日本語": "Japanese",
}

# ===== UI 文本翻译字典 =====
TRANSLATIONS = {
    # 页面标题
    "page_title": {
        "中文": "代码注释 Agent",
        "English": "Code Comment Agent",
        "日本語": "コードコメントエージェント",
    },
    # 顶部标题
    "app_title": {
        "中文": "# 📝 代码注释与 API 文档自动生成 Agent",
        "English": "# 📝 Code Comment & API Doc Auto-Generation Agent",
        "日本語": "# 📝 コードコメント・APIドキュメント自動生成エージェント",
    },
    "app_subtitle": {
        "中文": "粘贴代码或上传文件，AI 自动生成中文注释和 Markdown API 文档 · 支持 Python & Java",
        "English": "Paste code or upload files, AI auto-generates comments and Markdown API docs · Supports Python & Java",
        "日本語": "コードを貼り付けるかファイルをアップロード、AIが自動的にコメントとMarkdown APIドキュメントを生成・Python & Java対応",
    },
    # UI 语言选择
    "ui_lang_label": {
        "中文": "🌐 界面语言",
        "English": "🌐 UI Language",
        "日本語": "🌐 言語",
    },
    # 编程语言
    "prog_lang_label": {
        "中文": "🌐 编程语言",
        "English": "🌐 Programming Language",
        "日本語": "🌐 プログラミング言語",
    },
    # 输入区
    "input_section": {
        "中文": "### 📥 代码输入",
        "English": "### 📥 Code Input",
        "日本語": "### 📥 コード入力",
    },
    "upload_label": {
        "中文": "上传源代码文件",
        "English": "Upload source code file",
        "日本語": "ソースコードファイルをアップロード",
    },
    "editor_label": {
        "中文": "✏️ 代码编辑器",
        "English": "✏️ Code Editor",
        "日本語": "✏️ コードエディタ",
    },
    # 操作按钮
    "gen_btn": {
        "中文": "🚀 生成注释与文档",
        "English": "🚀 Generate Comments & Docs",
        "日本語": "🚀 コメントとドキュメントを生成",
    },
    "analyze_btn": {
        "中文": "🔍 分析代码",
        "English": "🔍 Analyze Code",
        "日本語": "🔍 コードを分析",
    },
    "cancel_btn": {
        "中文": "⏹️ 取消任务",
        "English": "⏹️ Cancel Task",
        "日本語": "⏹️ タスクをキャンセル",
    },
    # 输出 Tab
    "tab_annotated": {
        "中文": "📄 带注释的代码",
        "English": "📄 Annotated Code",
        "日本語": "📄 コメント付きコード",
    },
    "tab_docs": {
        "中文": "📚 API 文档",
        "English": "📚 API Docs",
        "日本語": "📚 APIドキュメント",
    },
    "tab_analysis": {
        "中文": "🔍 代码分析",
        "English": "🔍 Code Analysis",
        "日本語": "🔍 コード分析",
    },
    "tab_diff": {
        "中文": "🆚 代码差异 (Diff)",
        "English": "🆚 Code Diff",
        "日本語": "🆚 コード差分 (Diff)",
    },
    "tab_log": {
        "中文": "📋 处理日志",
        "English": "📋 Process Log",
        "日本語": "📋 処理ログ",
    },
    # 下载按钮
    "dl_src_btn": {
        "中文": "📥 下载注释后的代码",
        "English": "📥 Download Annotated Code",
        "日本語": "📥 コメント付きコードをダウンロード",
    },
    "dl_md_btn": {
        "中文": "📥 下载 Markdown 文档",
        "English": "📥 Download Markdown Docs",
        "日本語": "📥 Markdownドキュメントをダウンロード",
    },
    # 代码分析区
    "quality_title": {
        "中文": "### 📊 代码质量分析",
        "English": "### 📊 Code Quality Analysis",
        "日本語": "### 📊 コード品質分析",
    },
    "annotation_title": {
        "中文": "### 🎯 类型注解检查",
        "English": "### 🎯 Type Annotation Check",
        "日本語": "### 🎯 型アノテーションチェック",
    },
    "summary_title": {
        "中文": "### 📝 代码摘要",
        "English": "### 📝 Code Summary",
        "日本語": "### 📝 コードサマリー",
    },
    # 代码标签
    "output_code_label": {
        "中文": "代码",
        "English": "Code",
        "日本語": "コード",
    },
    # 分析/处理日志标签
    "analyze_log_label": {
        "中文": "分析日志",
        "English": "Analysis Log",
        "日本語": "分析ログ",
    },
    "process_log_label": {
        "中文": "处理日志",
        "English": "Process Log",
        "日本語": "処理ログ",
    },
    # 页脚
    "footer": {
        "中文": "Powered by DeepSeek LLM · Gradio 6.0 · 自动生成中文注释与文档",
        "English": "Powered by DeepSeek LLM · Gradio 6.0 · Auto-generate comments & docs",
        "日本語": "Powered by DeepSeek LLM · Gradio 6.0 · コメントとドキュメントを自動生成",
    },
    # ====== 批量处理新增 ======
    "batch_section": {
        "中文": "### 📦 批量处理（多文件 / ZIP 压缩包）",
        "English": "### 📦 Batch Process (Multi-files / ZIP)",
        "日本語": "### 📦 一括処理（複数ファイル / ZIP）",
    },
    "batch_upload_label": {
        "中文": "批量上传：多个 .py/.java 文件或整个 .zip 压缩包（含递归子目录）",
        "English": "Batch Upload: Multiple .py/.java files or a .zip archive (recursive subfolders)",
        "日本語": "一括アップロード：複数の .py/.java ファイル、または .zip 圧縮フォルダ（再帰的にサブフォルダを含む）",
    },
    "batch_gen_btn": {
        "中文": "🚀 批量生成注释并打包下载",
        "English": "🚀 Batch Generate & Download ZIP",
        "日本語": "🚀 一括コメント生成してZIPでダウンロード",
    },
    "batch_dl_btn": {
        "中文": "📥 下载批量处理结果 (ZIP)",
        "English": "📥 Download Batch Result (ZIP)",
        "日本語": "📥 一括処理結果をダウンロード (ZIP)",
    },
    "batch_cancel_btn": {
        "中文": "⏹️ 取消批量任务",
        "English": "⏹️ Cancel Batch",
        "日本語": "⏹️ 一括処理をキャンセル",
    },
    "batch_log_label": {
        "中文": "批量处理日志",
        "English": "Batch Process Log",
        "日本語": "一括処理ログ",
    },
    "style_section": {
        "中文": "### 🎨 注释风格选择",
        "English": "### 🎨 Comment Style",
        "日本語": "### 🎨 コメントスタイル",
    },
    "python_style_label": {
        "中文": "Python 注释风格",
        "English": "Python Docstring Style",
        "日本語": "Python ドキュメントスタイル",
    },
    "java_style_label": {
        "中文": "Java 注释风格",
        "English": "Java Javadoc Style",
        "日本語": "Java Javadoc スタイル",
    },
}


def t(key: str, lang: str) -> str:
    """获取指定语言的翻译文本

    Args:
        key: 翻译键
        lang: UI 语言（"中文" / "English" / "日本語"）

    Returns:
        str: 翻译后的文本，找不到时回退到中文
    """
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("中文", key))


def needs_translation(text: str, target_lang: str) -> bool:
    """快速判断文本是否可能需要翻译到目标语言

    通过字符集启发式判断，避免不必要的 LLM 调用。

    Args:
        text: 待检测文本
        target_lang: 目标语言代码（zh / en / ja）

    Returns:
        bool: 是否可能需要翻译
    """
    if not text:
        return False
    has_cjk = any('\u4e00' <= c <= '\u9fff' for c in text)
    has_kana = any('\u3040' <= c <= '\u30ff' for c in text)

    if target_lang == "en":
        # 目标英文：含中日韩字符或假名则需要翻译
        return has_cjk or has_kana
    if target_lang == "zh":
        # 目标中文：纯汉字（无假名）视为已是中文；含假名（日文）或纯英文则需要翻译
        return has_kana or not has_cjk
    if target_lang == "ja":
        # 目标日文：含假名视为已是日文；纯汉字（中文）或纯英文则需要翻译
        return not has_kana
    return False
