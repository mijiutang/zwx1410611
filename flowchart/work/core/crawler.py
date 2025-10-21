import json
from datetime import datetime
import re
import os

def parse_signal_content(content):
    """
    Parses the custom signal content string into a Python dictionary.
    """
    data = {}
    # Split the content by '}{' to get individual key-value blocks
    # and then re-add the curly braces for easier processing
    blocks = re.findall(r'\{[^}]+\}', content)

    for block in blocks:
        # Remove outer curly braces
        block_content = block[1:-1]
        if ':' in block_content:
            key, value = block_content.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Handle special cases like '商品详情' which is a list of dicts
            if key == "商品详情":
                # This is a simplified parsing for the given example
                # A more robust parser would be needed for complex nested structures
                item_details = []
                # Find all items within the 商品详情 block
                items = re.findall(r'\{[^}]+\}', value)
                for item_str in items:
                    item_dict = {}
                    # Remove outer curly braces for item
                    item_str_content = item_str[1:-1]
                    item_pairs = item_str_content.split(',')
                    for pair in item_pairs:
                        if '=' in pair:
                            item_key, item_value = pair.split('=', 1)
                            item_dict[item_key.strip()] = item_value.strip()
                    item_details.append(item_dict)
                data[key] = item_details
            elif key == "外卖运单状态变更记录":
                # Split by '→' and clean up
                data[key] = [s.strip() for s in value.split('→') if s.strip()]
            else:
                data[key] = value
    return data

def get_signal_data(file_path="C:\\Users\\Administrator\\Desktop\\flowchart\\信号.txt"):
    """
    Reads the content of the signal file, parses it,
    and returns the original content and parsed data.
    """
    original_content = ""
    parsed_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        parsed_data = parse_signal_content(original_content)

        return original_content, parsed_data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return "", {}
    except Exception as e:
        print(f"Error processing file: {e}")
        return "", {}