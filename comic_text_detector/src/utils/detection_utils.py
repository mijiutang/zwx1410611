"""
检测相关的辅助函数
"""

import numpy as np
from typing import List, Dict, Any

def calculate_containment_ratio(box_small, box_large):
    """计算小框在大框中的包含比例"""
    x1, y1, x2, y2 = box_small
    x1_2, y1_2, x2_2, y2_2 = box_large
    
    # 计算交集
    inter_x1 = max(x1, x1_2)
    inter_y1 = max(y1, y1_2)
    inter_x2 = min(x2, x2_2)
    inter_y2 = min(y2, y2_2)
    
    if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
        return 0.0
    
    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    small_area = (x2 - x1) * (y2 - y1)
    
    return inter_area / small_area if small_area > 0 else 0.0


def filter_and_merge_boxes(text_regions, config_params):
    """过滤和合并检测框"""
    if not config_params.get('enable_box_filter', True):
        return text_regions
    
    min_box_width = config_params.get('min_box_width', 10)
    min_box_height = config_params.get('min_box_height', 10)
    containment_thresh = config_params.get('containment_thresh', 0.8)
    
    print(f"开始框处理，共有{len(text_regions)}个框")
    
    # 1. 过滤小框
    filtered_regions = []
    for i, region in enumerate(text_regions):
        x1, y1, x2, y2 = region['bbox']
        width = x2 - x1
        height = y2 - y1
        print(f"框{i}: 位置[{x1},{y1},{x2},{y2}], 尺寸{width}x{height}")
        
        if width >= min_box_width or height >= min_box_height:
            filtered_regions.append(region)
        else:
            print(f"过滤掉小框{i}")
    
    if len(filtered_regions) <= 1:
        print("框数量<=1，无需合并")
        return filtered_regions
    
    # 2. 处理包含关系
    to_remove = set()
    for i in range(len(filtered_regions)):
        if i in to_remove:
            continue
        for j in range(len(filtered_regions)):
            if i == j or j in to_remove:
                continue
            
            box_i = filtered_regions[i]['bbox']
            box_j = filtered_regions[j]['bbox']
            
            containment_i_in_j = calculate_containment_ratio(box_i, box_j)
            if containment_i_in_j > containment_thresh:
                to_remove.add(i)
                print(f"移除被包含的框{i}: 包含比例{containment_i_in_j:.3f}")
                break
    
    # 移除被包含的框
    filtered_regions = [region for i, region in enumerate(filtered_regions) if i not in to_remove]
    print(f"包含关系处理后，剩余{len(filtered_regions)}个框")

    return filtered_regions