import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gradio as gr

print("=== 验证 gr.update() 修复 ===")

from ui import _update_code_language, _update_file_types

r1 = _update_code_language('Java')
r2 = _update_code_language('Python')
r3 = _update_file_types('Java')
r4 = _update_file_types('Python')

print(f"Java code update: type={type(r1).__name__}, value={r1}")
print(f"Python code update: type={type(r2).__name__}, value={r2}")
print(f"Java file update: type={type(r3).__name__}, value={r3}")
print(f"Python file update: type={type(r4).__name__}, value={r4}")

assert r1.get('language') == 'java'
assert r2.get('language') == 'python'
assert r3.get('file_types') == ['.java']
assert r4.get('file_types') == ['.py']
print("✓ gr.update() 返回值正确")

print("\n=== 验证 UI 创建 ===")
from ui import create_ui, CUSTOM_CSS
demo = create_ui()
print("✓ UI 创建成功（无报错）")

print("\n=== 验证事件绑定 ===")
with gr.Blocks() as test:
    code = gr.Code(language='python')
    file_comp = gr.File(file_types=['.py'])
    lang = gr.Dropdown(choices=['Python', 'Java'], value='Python')
    lang.change(
        fn=lambda x: (_update_code_language(x), _update_file_types(x)),
        outputs=[code, file_comp]
    )
print("✓ 事件绑定成功")

print("\n=== ALL TESTS PASSED ===")
