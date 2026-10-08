# -*- coding: utf-8 -*-
"""Internal owner of the unchanged Gradio stylesheet."""

# ==================== 自定义 CSS ====================
CUSTOM_CSS = """
/* ===== 全局基础 ===== */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', system-ui, sans-serif !important;
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
    font-family: 'JetBrains Mono', 'SF Mono', 'Monaco', 'Menlo', 'Fira Code', 'Consolas', monospace !important;
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

/* ===== 隐藏原生下载按钮；保留 Gradio Code 的 Copy 能力 ===== */
.code-container .gr-code-download,
.code-container [aria-label*="Download"],
.code-container [aria-label*="下载"],
.code-header button.download {
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

/* ===== v2.4.1 macOS 滚动条适配（overlay 风格）===== */
/* macOS 默认使用 overlay 滚动条，宽 10px 在 macOS 上偏粗，细化为 8px */
@media (-webkit-min-device-pixel-ratio: 1) and (pointer: fine) {
    .code-container .cm-scroller::-webkit-scrollbar,
    .scrollable-md::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }
}
/* macOS 触控板/鼠标悬停时滚动条才显示，非悬停时半透明 */
.code-container .cm-scroller::-webkit-scrollbar:vertical {
    -webkit-appearance: none !important;
    appearance: none !important;
}

/* ===== v2.4.1 响应式自适应（平板 768px / 手机 480px / 小手机 360px 三档断点）===== */

/* --- 平板（iPad 768px ~ 1024px）：适度缩小 --- */
@media (max-width: 1024px) {
    .gradio-container {
        max-width: 100% !important;
        padding: 16px 12px !important;
    }
    .app-header {
        padding: 20px 24px !important;
    }
    .app-header h1 {
        font-size: 22px !important;
    }
    .header-lang-switcher {
        min-width: 140px !important;
    }
    .code-container {
        height: 500px !important;
        min-height: 300px !important;
    }
    .code-container > div,
    .code-container .cm-editor,
    .code-container .cm-scroller,
    .code-container .cm-content {
        min-height: 300px !important;
        max-height: 500px !important;
    }
}

/* --- 手机（≤768px）：垂直堆叠 + 全宽 --- */
@media (max-width: 768px) {
    .gradio-container {
        max-width: 100% !important;
        padding: 10px 8px !important;
    }
    /* 顶部标题 + 语言切换器垂直排列 */
    .header-row {
        flex-direction: column !important;
        align-items: stretch !important;
        gap: 12px !important;
    }
    .header-lang-switcher {
        min-width: 100% !important;
        max-width: 100% !important;
    }
    .app-header {
        padding: 16px 18px !important;
        border-radius: 12px !important;
    }
    .app-header h1 {
        font-size: 19px !important;
    }
    .app-header h2, .app-header p {
        font-size: 12px !important;
    }
    /* 卡片减小内边距 */
    .card-section {
        padding: 14px 12px !important;
        margin-bottom: 12px !important;
        border-radius: 10px !important;
    }
    /* 等宽列在手机上垂直堆叠 */
    .equal-width {
        flex-direction: column !important;
    }
    .equal-width > div {
        flex: none !important;
        width: 100% !important;
    }
    /* 代码编辑器高度适配手机屏幕 */
    .code-container {
        height: 380px !important;
        min-height: 250px !important;
    }
    .code-container > div,
    .code-container .cm-editor,
    .code-container .cm-scroller,
    .code-container .cm-content {
        min-height: 250px !important;
        max-height: 380px !important;
    }
    .code-container .cm-editor {
        font-size: 13px !important;
        border-radius: 8px !important;
    }
    /* 滚动容器 */
    .scrollable-md {
        max-height: 400px !important;
        min-height: 150px !important;
        padding: 10px 12px !important;
        font-size: 13px !important;
    }
    /* 操作按钮：全宽 + 缩小内边距 */
    .action-btn {
        padding: 10px 16px !important;
        font-size: 14px !important;
        border-radius: 8px !important;
        width: 100% !important;
    }
    /* 按钮行垂直排列 */
    .gradio-container .form > div:has(.action-btn) {
        flex-direction: column !important;
        gap: 8px !important;
    }
    /* Tab 导航可水平滚动 + 字号缩小 */
    .gradio-container .tab-nav {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        -webkit-overflow-scrolling: touch !important;
    }
    .gradio-container .tab-nav button {
        padding: 8px 12px !important;
        font-size: 13px !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
    }
    /* Tab 内容区 */
    .gradio-container .tabitem {
        min-height: 250px !important;
        padding-top: 12px !important;
    }
    /* 下载按钮行垂直排列 */
    .dl-btn-row {
        flex-direction: column !important;
        gap: 10px !important;
    }
    .dl-btn-row > div {
        flex: none !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    .dl-download-btn {
        height: 42px !important;
        font-size: 14px !important;
        border-radius: 8px !important;
    }
    /* 文件上传区 */
    .gradio-container .gr-file,
    .gradio-container .upload-container {
        min-height: 120px !important;
    }
    /* 页脚 */
    .app-footer {
        font-size: 11px !important;
        padding: 14px 8px !important;
    }
    /* 大纲折叠区更紧凑 */
    .outline-sidebar summary {
        padding: 6px 8px !important;
        font-size: 13px !important;
    }
    .outline-sidebar details > ul {
        padding: 4px 0 6px 20px !important;
    }
}

/* --- 小手机（≤480px：iPhone SE / Android compact）进一步压缩 --- */
@media (max-width: 480px) {
    .gradio-container {
        padding: 6px 4px !important;
    }
    .app-header {
        padding: 12px 14px !important;
        border-radius: 10px !important;
    }
    .app-header h1 {
        font-size: 17px !important;
    }
    .app-header h2, .app-header p {
        font-size: 11px !important;
    }
    .card-section {
        padding: 10px 8px !important;
        margin-bottom: 10px !important;
        border-radius: 8px !important;
    }
    .code-container {
        height: 300px !important;
        min-height: 200px !important;
    }
    .code-container > div,
    .code-container .cm-editor,
    .code-container .cm-scroller,
    .code-container .cm-content {
        min-height: 200px !important;
        max-height: 300px !important;
    }
    .code-container .cm-editor {
        font-size: 12px !important;
    }
    .scrollable-md {
        max-height: 300px !important;
        min-height: 100px !important;
        padding: 8px 10px !important;
        font-size: 12px !important;
    }
    .action-btn {
        padding: 9px 12px !important;
        font-size: 13px !important;
    }
    .gradio-container .tab-nav button {
        padding: 6px 10px !important;
        font-size: 12px !important;
    }
    .gradio-container label {
        font-size: 12px !important;
        margin-bottom: 4px !important;
    }
    .dl-download-btn {
        height: 38px !important;
        font-size: 13px !important;
    }
}

/* --- 触控设备（无 hover）：禁用悬浮动效，减少误触 --- */
@media (hover: none) and (pointer: coarse) {
    .card-section:hover {
        transform: none !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.03) !important;
    }
    .action-btn:hover {
        transform: none !important;
        box-shadow: none !important;
    }
    .dl-download-btn:hover {
        transform: none !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    .outline-sidebar summary:hover {
        background: transparent !important;
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
    font-family: 'JetBrains Mono', 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace !important;
}
.outline-sidebar summary small,
.outline-sidebar details > ul > li small {
    color: #9ca3af !important;
    font-size: 11px !important;
}
"""
