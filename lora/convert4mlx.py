#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import argparse
from pathlib import Path
from tqdm import tqdm
import chardet
import docx
import markdown

# dependencies: pip install python-docx chardet markdown tqdm
# usage: python convert4mlx.py  --repo_path /path/to/source/code  --doc_path /path/to/documents  --output training_data.jsonl
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def read_code_file(file_path):
    try:
        encoding = detect_encoding(file_path)
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None

def read_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {str(e)}")
        return None

def read_markdown(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
            return markdown.markdown(md_text)  # Convert to plain text
    except Exception as e:
        print(f"Error reading Markdown {file_path}: {str(e)}")
        return None

def process_files(root_dir, extensions, file_processor):
    processed = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                content = file_processor(file_path)
                if content:
                    processed.append({
                        "text": content,
                        "meta": {
                            "file_path": file_path,
                            "file_type": Path(file_path).suffix
                        }
                    })
    return processed

def main():
    parser = argparse.ArgumentParser(description='MLX Training Data Converter')
    parser.add_argument('--repo_path', type=str, required=True, help='Local path to source code repository')
    parser.add_argument('--doc_path', type=str, required=True, help='Local path to knowledge base documents')
    parser.add_argument('--output', type=str, default='training_data.jsonl', help='Output JSONL file path')
    
    args = parser.parse_args()

    # 处理源代码文件
    code_extensions = ['.kt', '.java', '.js', '.ts', '.cpp', '.h', '.c','.jsx','.tsx','.m','.mm','.hpp']
    code_data = process_files(args.repo_path, code_extensions, read_code_file)

    # 处理文档文件
    doc_ext_map = {
        '.docx': read_docx,
        '.md': read_markdown,
        '.txt': read_code_file
    }
    doc_data = []
    for root, _, files in os.walk(args.doc_path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = Path(file_path).suffix.lower()
            if ext in doc_ext_map:
                content = doc_ext_map[ext](file_path)
                if content:
                    doc_data.append({
                        "text": content,
                        "meta": {
                            "file_path": file_path,
                            "file_type": ext
                        }
                    })

    # 合并数据并保存
    all_data = code_data + doc_data
    with open(args.output, 'w', encoding='utf-8') as f:
        for item in tqdm(all_data, desc='Writing JSONL'):
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"Successfully converted {len(all_data)} items to {args.output}")

if __name__ == "__main__":
    main()