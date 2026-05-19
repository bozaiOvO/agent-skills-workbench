#!/usr/bin/env python3
"""
女娲本地语料预处理：大规模口语转录文本清洗

处理场景：用户丢来几百个直播/播客/视频的ASR转录文本文件，
在女娲Phase 1读取前先做机械清洗，把噪音砍掉。

三步漏斗：
  1. ASR结巴修复 + 规则过滤（砍废话短句、互动噪音）
  2. 文本去重（MinHash近似去重，需要datasketch；不装也能跑，降级为精确hash去重）
  3. 高价值段落提取（按长度筛选，长段落通常包含完整论述）

用法：
  python3 preprocess_corpus.py <输入目录> <输出目录>

输入：一个文件夹，里面是 .txt 转录文件（每个文件一场直播/访谈）
输出：
  - cleaned_corpus.txt          合并清洗后的全文（供Agent阅读）
  - high_value_segments.txt     高价值长段落（优先给Agent看的精华）
  - preprocess_report.txt       清洗统计报告
"""

import os
import sys
import re
import hashlib
from collections import OrderedDict

# ==================== 配置 ====================

# 规则过滤：短于此长度的段落直接丢弃
MIN_SEGMENT_LEN = 15

# 高价值段落：长于此长度的段落单独提取
HIGH_VALUE_MIN_LEN = 200

# 通用直播/口播噪音正则（不绑定特定主播）
NOISE_PATTERNS = [
    r"感谢.*?(送的|礼物|打赏|刷的|嘉年华|穿云箭|火箭)",
    r"感谢.*?(关注|点赞|收藏|转发)",
    r"欢迎.*?(来到|进入).*?直播间",
    r"(加|发|看)(私信|微信|v信|VX)",
    r"(连麦吗|不连麦|想连麦|来连个麦)",
    r"(点个关注|点点关注|关注一下|帮我点个)",
    r"(双击|点亮|小红心|小黄车|橱窗)",
    r"(信号|网络|卡了|画面|声音).*(不好|卡顿|听不到|看不到)",
    r"(测试|试一下|能听到吗|能看到吗|有声音吗)",
    r"^(嗯|啊|哦|嗨|哈|呵|喂|好的|行|对){1,}[，。！？]?$",
    r"^.{1,5}$",  # 5个字以下的独立行
]
COMPILED_NOISE = [re.compile(p) for p in NOISE_PATTERNS]

# ASR结巴修复正则
STUTTER_FIXES = [
    # 单字结巴：我我我觉得 → 我觉得
    (re.compile(r'([我你他她它这那对就是的了呢啊嗯哦哈吧么])\1{1,}'), r'\1'),
    # 双字结巴：这个这个这个 → 这个
    (re.compile(r'(这个){2,}'), '这个'),
    (re.compile(r'(那个){2,}'), '那个'),
    (re.compile(r'(然后){2,}'), '然后'),
    (re.compile(r'(就是){2,}'), '就是'),
    (re.compile(r'(所以){2,}'), '所以'),
    (re.compile(r'(但是){2,}'), '但是'),
    (re.compile(r'(因为){2,}'), '因为'),
    (re.compile(r'(其实){2,}'), '其实'),
    # 连续标点
    (re.compile(r'[，。！？、]{3,}'), '，'),
]


def fix_stutter(text):
    """修复ASR转录中的结巴和语气词重复"""
    for pattern, replacement in STUTTER_FIXES:
        text = pattern.sub(replacement, text)
    return text.strip()


def is_noise(text):
    """判断一行是否是直播噪音"""
    text = text.strip()
    if len(text) < MIN_SEGMENT_LEN:
        return True
    for pattern in COMPILED_NOISE:
        if pattern.search(text):
            return True
    return False


def split_to_segments(text):
    """将长文本按自然段落分割。

    口语转录通常没有换行，是一整坨文字。
    策略：先按换行分段，如果段落过长（>500字），
    再按句号/问号/感叹号做二次切分。
    """
    # 先按换行分
    lines = text.split('\n')
    raw_blocks = []
    current = []

    for line in lines:
        line = line.strip()
        if not line:
            if current:
                raw_blocks.append(''.join(current))
                current = []
        else:
            current.append(line)

    if current:
        raw_blocks.append(''.join(current))

    # 对过长的块按句子边界二次切分
    segments = []
    for block in raw_blocks:
        if len(block) <= 500:
            segments.append(block)
        else:
            # 检查是否有标点可供切分
            has_punct = bool(re.search(r'[。？！\?\!]', block))
            if has_punct:
                # 按句末标点切分，保留标点
                sentences = re.split(r'(?<=[。？！\?\!])', block)
                chunk = ''
                for sent in sentences:
                    if not sent.strip():
                        continue
                    if len(chunk) + len(sent) > 500 and chunk:
                        segments.append(chunk.strip())
                        chunk = sent
                    else:
                        chunk += sent
                if chunk.strip():
                    segments.append(chunk.strip())
            else:
                # 无标点的ASR原始文本：按逗号/顿号切分，拼成~300字的块
                # 如果连逗号都没有，按固定长度强制切
                parts = re.split(r'(?<=[，,、])', block)
                if len(parts) <= 1:
                    # 完全无标点，按300字强制切
                    for i in range(0, len(block), 300):
                        seg = block[i:i+300].strip()
                        if seg:
                            segments.append(seg)
                else:
                    chunk = ''
                    for part in parts:
                        if not part.strip():
                            continue
                        if len(chunk) + len(part) > 300 and chunk:
                            segments.append(chunk.strip())
                            chunk = part
                        else:
                            chunk += part
                    if chunk.strip():
                        segments.append(chunk.strip())

    return segments


def text_hash(text):
    """计算文本的简单hash用于精确去重"""
    normalized = re.sub(r'\s+', '', text)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def try_minhash_dedup(segments, threshold=0.85):
    """尝试用MinHash去重，如果datasketch没装就降级为精确hash去重"""
    try:
        from datasketch import MinHash, MinHashLSH
        lsh = MinHashLSH(threshold=threshold, num_perm=128)
        unique = []
        dup_count = 0

        for idx, seg in enumerate(segments):
            m = MinHash(num_perm=128)
            ngrams = [seg[i:i+3] for i in range(len(seg)-2)] if len(seg) >= 3 else [seg]
            for ng in ngrams:
                m.update(ng.encode('utf-8'))

            if not lsh.query(m):
                lsh.insert(str(idx), m)
                unique.append(seg)
            else:
                dup_count += 1

        return unique, dup_count, "MinHash"

    except ImportError:
        # 降级：精确hash去重
        seen = OrderedDict()
        dup_count = 0
        for seg in segments:
            h = text_hash(seg)
            if h not in seen:
                seen[h] = seg
            else:
                dup_count += 1
        return list(seen.values()), dup_count, "精确hash"


def process(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # 收集所有txt文件
    txt_files = sorted([
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.endswith('.txt')
    ])

    if not txt_files:
        print(f"输入目录 {input_dir} 中没有找到 .txt 文件")
        sys.exit(1)

    print(f"找到 {len(txt_files)} 个文本文件")

    # Step 1: 读取 + 结巴修复 + 规则过滤
    all_segments = []
    stats = {
        'total_files': len(txt_files),
        'total_raw_segments': 0,
        'noise_dropped': 0,
        'stutter_fixed': 0,
    }

    for fpath in txt_files:
        with open(fpath, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        segments = split_to_segments(raw_text)
        stats['total_raw_segments'] += len(segments)

        for seg in segments:
            original = seg
            seg = fix_stutter(seg)
            if seg != original:
                stats['stutter_fixed'] += 1

            if is_noise(seg):
                stats['noise_dropped'] += 1
                continue

            all_segments.append(seg)

    print(f"规则过滤后: {len(all_segments)} 段 (丢弃 {stats['noise_dropped']} 段噪音)")

    # Step 2: 去重
    unique_segments, dup_count, method = try_minhash_dedup(all_segments)
    stats['dedup_method'] = method
    stats['dedup_dropped'] = dup_count
    print(f"{method}去重后: {len(unique_segments)} 段 (剔除 {dup_count} 段重复)")

    # Step 3: 高价值段落提取
    high_value = [seg for seg in unique_segments if len(seg) >= HIGH_VALUE_MIN_LEN]
    stats['after_clean'] = len(unique_segments)
    stats['high_value'] = len(high_value)
    print(f"高价值段落 (>={HIGH_VALUE_MIN_LEN}字): {len(high_value)} 段")

    # 输出
    cleaned_path = os.path.join(output_dir, 'cleaned_corpus.txt')
    with open(cleaned_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(unique_segments))

    hv_path = os.path.join(output_dir, 'high_value_segments.txt')
    with open(hv_path, 'w', encoding='utf-8') as f:
        f.write('\n\n---\n\n'.join(high_value))

    report_path = os.path.join(output_dir, 'preprocess_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("女娲本地语料预处理报告\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"输入文件数: {stats['total_files']}\n")
        f.write(f"原始段落数: {stats['total_raw_segments']}\n")
        f.write(f"结巴修复数: {stats['stutter_fixed']}\n")
        f.write(f"噪音丢弃数: {stats['noise_dropped']}\n")
        f.write(f"去重方式:   {stats['dedup_method']}\n")
        f.write(f"重复丢弃数: {stats['dedup_dropped']}\n")
        f.write(f"清洗后段落: {stats['after_clean']}\n")
        f.write(f"高价值段落: {stats['high_value']} (>={HIGH_VALUE_MIN_LEN}字)\n")
        f.write(f"\n漏斗: {stats['total_raw_segments']}")
        f.write(f" → -{stats['noise_dropped']}噪音")
        f.write(f" → -{stats['dedup_dropped']}重复")
        f.write(f" → {stats['after_clean']} 段\n")

    print(f"\n输出文件:")
    print(f"  {cleaned_path}")
    print(f"  {hv_path}")
    print(f"  {report_path}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 preprocess_corpus.py <输入目录> <输出目录>")
        print("输入: 包含.txt转录文件的目录")
        print("输出: cleaned_corpus.txt + high_value_segments.txt + preprocess_report.txt")
        sys.exit(1)

    process(sys.argv[1], sys.argv[2])
