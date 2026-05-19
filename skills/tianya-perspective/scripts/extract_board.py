#!/usr/bin/env python3
"""
天涯板块文本提取脚本
用法: python3 extract_board.py <板块目录> <输出文件>

提取指定板块目录下所有PDF/epub/txt/docx的文本，
为每个文件生成摘要级别的提取（前N页/字），
最终输出一个合并的markdown文件用于分析。
"""

import sys
import os

def extract_pdf(filepath, max_pages=30):
    """提取PDF前max_pages页的文本"""
    import pymupdf
    try:
        doc = pymupdf.open(filepath)
        total_pages = len(doc)
        pages_to_read = min(max_pages, total_pages)
        texts = []
        for i in range(pages_to_read):
            text = doc[i].get_text()
            if text.strip():
                texts.append(text.strip())
        doc.close()
        return "\n\n".join(texts), total_pages
    except Exception as e:
        return f"[提取失败: {e}]", 0

def extract_txt(filepath, max_chars=50000):
    """提取txt文件前max_chars字符"""
    try:
        for enc in ['utf-8', 'gbk', 'gb18030', 'latin-1']:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    text = f.read(max_chars)
                return text, len(text)
            except UnicodeDecodeError:
                continue
        return "[编码无法识别]", 0
    except Exception as e:
        return f"[提取失败: {e}]", 0

def extract_epub(filepath, max_chars=50000):
    """提取epub文本（简单方式）"""
    try:
        import zipfile
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.texts = []
            def handle_data(self, data):
                self.texts.append(data)
        
        with zipfile.ZipFile(filepath, 'r') as z:
            all_text = []
            for name in z.namelist():
                if name.endswith(('.html', '.xhtml', '.htm')):
                    try:
                        content = z.read(name).decode('utf-8', errors='ignore')
                        parser = TextExtractor()
                        parser.feed(content)
                        all_text.extend(parser.texts)
                    except:
                        pass
            text = "\n".join(all_text)[:max_chars]
            return text, len(text)
    except Exception as e:
        return f"[提取失败: {e}]", 0

def extract_docx(filepath, max_chars=50000):
    """提取docx文本（简单方式）"""
    try:
        import zipfile
        import re
        with zipfile.ZipFile(filepath, 'r') as z:
            if 'word/document.xml' in z.namelist():
                content = z.read('word/document.xml').decode('utf-8', errors='ignore')
                text = re.sub(r'<[^>]+>', '', content)
                text = re.sub(r'\s+', '\n', text)[:max_chars]
                return text, len(text)
        return "[无法读取]", 0
    except Exception as e:
        return f"[提取失败: {e}]", 0

def main():
    if len(sys.argv) < 3:
        print("用法: python3 extract_board.py <板块目录> <输出文件>")
        sys.exit(1)
    
    board_dir = sys.argv[1]
    output_file = sys.argv[2]
    board_name = os.path.basename(board_dir)
    
    # 收集所有可处理的文件
    files = []
    for root, dirs, filenames in os.walk(board_dir):
        for f in sorted(filenames):
            if f.startswith('.'):
                continue
            ext = f.rsplit('.', 1)[-1].lower() if '.' in f else ''
            if ext in ('pdf', 'txt', 'epub', 'docx', 'doc', 'md'):
                files.append(os.path.join(root, f))
    
    print(f"板块: {board_name}, 共 {len(files)} 个可处理文件")
    
    output_parts = []
    output_parts.append(f"# 天涯合集 · {board_name} 板块文本提取\n")
    output_parts.append(f"共 {len(files)} 个文件\n\n---\n")
    
    for i, filepath in enumerate(files, 1):
        filename = os.path.basename(filepath)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        print(f"  [{i}/{len(files)}] {filename}...", end=" ", flush=True)
        
        if ext == 'pdf':
            text, info = extract_pdf(filepath, max_pages=20)
            meta = f"PDF, {info}页"
        elif ext == 'txt' or ext == 'md':
            text, info = extract_txt(filepath)
            meta = f"TXT, {info}字符"
        elif ext == 'epub':
            text, info = extract_epub(filepath)
            meta = f"EPUB, {info}字符"
        elif ext in ('docx', 'doc'):
            if ext == 'docx':
                text, info = extract_docx(filepath)
                meta = f"DOCX, {info}字符"
            else:
                text = "[.doc格式暂不支持直接提取]"
                meta = "DOC"
        else:
            text = "[不支持的格式]"
            meta = ext
        
        # 截断过长的文本（每篇最多保留15000字符用于分析）
        if len(text) > 15000:
            text = text[:15000] + "\n\n...[截断，原文更长]..."
        
        output_parts.append(f"\n## {i}. {filename}\n")
        output_parts.append(f"**格式**: {meta}\n")
        output_parts.append(f"\n{text}\n")
        output_parts.append("\n---\n")
        
        print(f"OK ({meta})")
    
    # 写入输出文件
    full_output = "\n".join(output_parts)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_output)
    
    print(f"\n完成！输出: {output_file} ({len(full_output)} 字符)")

if __name__ == "__main__":
    main()
