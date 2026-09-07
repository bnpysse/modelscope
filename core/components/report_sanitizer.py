# -*- coding: utf-8 -*-
"""
天衍五维 · Markdown 与研报视觉净化渲染器
用于将大模型输出中的字符边框 (ASCII Box)、错乱代码块转换为高对比度、军工级科技感卡片
"""

import re


def sanitize_ai_report_markdown(content: str) -> str:
    """
    清理大模型输出中因为中英文字符等宽问题导致参差不齐的 ASCII 边框字符，
    并将其自愈为优雅的现代 Markdown 战术区块。
    """
    if not content or not isinstance(content, str):
        return ""

    # 1. 消除常见的字符方框边缘: ┌ ┐ └ ┘ ├ ┤ ─ │ ╔ ╗ ╚ ╝ ║ ═ ┃ ━ ┏ ┓ ┗ ┛ 等
    box_chars = r"[┌┐└┘├┤─│╔╗╚╝║═┃━┏┓┗┛┼┬┴╭╮╯╰|]{3,}"
    
    # 2. 将包含密集 ASCII 画框的 ``` 代码块转换为整齐的列表/提示卡片
    def clean_code_block(match):
        block_text = match.group(1)
        lines = block_text.strip().split("\n")
        cleaned_lines = []
        for line in lines:
            # 过滤纯画框横线
            line_sub = re.sub(r"^[┌┐└┘├┤─│╔╗╚╝║═┃━┏┓┗┛┼┬┴╭╮╯╰\s\-_=|+]+$", "", line)
            if not line_sub.strip():
                continue
            # 去除两侧的竖线边框
            line_clean = re.sub(r"^[│║┃|]+\s*", "", line)
            line_clean = re.sub(r"\s*[│║┃|]+$", "", line_clean)
            if line_clean.strip():
                # 转换为整齐的项目符号
                cleaned_lines.append(f"- {line_clean.strip()}")
        
        if cleaned_lines:
            return "\n" + "\n".join(cleaned_lines) + "\n"
        return ""

    # 针对 ```text 或 ``` 代码块中的 ASCII 边框执行清洗
    processed = re.sub(r"```(?:text|plain)?\s*([\s\S]*?)```", clean_code_block, content)
    
    # 针对裸露在正文中的孤立边框符号进行修剪
    processed = re.sub(r"^[┌└├╔╚┏┗].*?[┐┘┤╗╝┓┛]$", "", processed, flags=re.MULTILINE)
    processed = re.sub(r"^[│║┃|]\s*", "- ", processed, flags=re.MULTILINE)
    processed = re.sub(r"\s*[│║┃|]$", "", processed, flags=re.MULTILINE)
    processed = re.sub(r"^[─═━\-_=]{4,}$", "", processed, flags=re.MULTILINE)
    
    # 压缩连续多余空行
    processed = re.sub(r"\n{3,}", "\n\n", processed)

    return processed.strip()
