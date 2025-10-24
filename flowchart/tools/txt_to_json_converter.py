#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT to JSON Converter
将包含键值对的TXT文件转换为JSON格式
"""

import json
import os
import re
import argparse
import sys


def parse_signal_content(content):
    """
    解析规则（更新，支持多行块）：
    - 支持单行 {key:value} 和跨多行的 {key: ... \n ... }
    - 在每个 {...} 中，第一次出现的 ':' 将 key 与 value 分隔，之后的 ':' 都属于 value
    - value 不再进一步解析，作为字符串原样保存（保留换行）
    """
    result = {}
    if not content:
        return result

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # 如果该行同时包含 { 和 }，优先取该行内的内容
        if '{' in line and '}' in line and line.find('{') < line.rfind('}'):
            start = line.find('{')
            end = line.rfind('}')
            inner = line[start + 1:end].strip()
            i += 1
        # 如果该行包含 '{' 但没有 '}'，收集后续行直到找到 '}'
        elif '{' in line and '}' not in line:
            start = line.find('{')
            buf = line[start + 1:]  # 从 { 之后开始
            j = i + 1
            closed = False
            while j < len(lines):
                l = lines[j]
                if '}' in l:
                    endpos = l.rfind('}')
                    buf += '\n' + l[:endpos]
                    closed = True
                    break
                else:
                    buf += '\n' + l
                j += 1
            if not closed:
                # 找不到闭合大括号，跳过这个块
                i = j
                continue
            inner = buf.strip()
            i = j + 1
        # 如果该行没有 '{'，但可能是 '...} ' 行（没有开头），跳过
        else:
            i += 1
            continue

        # 按第一次出现的 ':' 分割 key/value
        idx = inner.find(':')
        if idx == -1:
            key = inner.strip()
            value = ""
        else:
            key = inner[:idx].strip()
            value = inner[idx + 1:].strip()

        # 移除成对引号（若有）
        if (len(key) >= 2) and ((key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'"))):
            key = key[1:-1]
        if (len(value) >= 2) and ((value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))):
            value = value[1:-1]

        result[key] = value

    return result


def convert_txt_to_json(txt_file_path, json_file_path=None):
    """
    将TXT文件转换为JSON文件
    
    Args:
        txt_file_path (str): 输入的TXT文件路径
        json_file_path (str): 输出的JSON文件路径，如果为None则自动生成
    """
    # 如果未指定输出文件路径，则自动生成
    if json_file_path is None:
        base_name = os.path.splitext(txt_file_path)[0]
        json_file_path = base_name + '.json'
    
    # 尝试不同的编码读取TXT文件
    content = None
    for encoding in ['utf-8', 'gbk', 'gb2312']:
        try:
            with open(txt_file_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print(f"错误: 无法读取文件 {txt_file_path}，可能的编码问题")
        return False
    
    # 解析内容
    try:
        parsed_data = parse_signal_content(content)
    except ValueError as e:
        print(f"解析错误: {e}")
        return False
    
    # 写入JSON文件
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
    
    print(f"成功转换: {txt_file_path} -> {json_file_path}")
    return True


def batch_convert_txt_to_json(input_dir, output_dir=None):
    """
    批量将目录中的TXT文件转换为JSON文件
    
    Args:
        input_dir (str): 包含TXT文件的输入目录
        output_dir (str): 输出JSON文件的目录，如果为None则使用输入目录
    """
    if output_dir is None:
        output_dir = input_dir
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有TXT文件
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"在目录 {input_dir} 中未找到TXT文件")
        return
    
    success_count = 0
    for txt_file in txt_files:
        txt_file_path = os.path.join(input_dir, txt_file)
        json_file_path = os.path.join(output_dir, os.path.splitext(txt_file)[0] + '.json')
        
        if convert_txt_to_json(txt_file_path, json_file_path):
            success_count += 1
    
    print(f"批量转换完成: {success_count}/{len(txt_files)} 个文件转换成功")


def main():
    parser = argparse.ArgumentParser(description='TXT to JSON Converter')
    parser.add_argument('input', help='输入TXT文件路径或包含TXT文件的目录')
    parser.add_argument('-o', '--output', help='输出JSON文件路径或目录')
    
    args = parser.parse_args()
    
    # 检查输入路径是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入路径 {args.input} 不存在")
        sys.exit(1)
    
    # 如果输入是文件
    if os.path.isfile(args.input):
        if args.input.endswith('.txt'):
            convert_txt_to_json(args.input, args.output)
        else:
            print("错误: 输入文件必须是TXT格式")
            sys.exit(1)
    # 如果输入是目录
    elif os.path.isdir(args.input):
        batch_convert_txt_to_json(args.input, args.output)
    else:
        print("错误: 输入路径既不是文件也不是目录")
        sys.exit(1)


if __name__ == '__main__':
    main()