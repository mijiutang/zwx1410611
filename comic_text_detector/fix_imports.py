import cv2
import numpy as np
import json
import os
from pathlib import Path

def extract_text_regions_from_json(json_file_path, output_dir="output_text_blocks"):
    """
    根据JSON文件中的文本行坐标提取文本区域：
    1. 原图文字行以外部分涂白
    2. 按 bbox 裁剪每个文本块，保存到指定文件夹
    """
    
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取原图路径和图片名
    image_path = data['image_path']
    image_name = data['image_name']
    
    # 检查原图是否存在
    if not os.path.exists(image_path):
        print(f"原图不存在: {image_path}")
        return
    
    # 读取原图
    original_img = cv2.imread(image_path)
    if original_img is None:
        print(f"无法读取图像: {image_path}")
        return
    
    height, width = original_img.shape[:2]
    
    # 创建白色背景图像
    result_img = np.full((height, width, 3), 255, dtype=np.uint8)
    
    # 创建掩码
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # 创建输出文件夹
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理每个文本区域
    for idx, region in enumerate(data['text_regions']):
        lines = region['lines']
        
        # 处理每条文本行
        for line in lines:
            points = np.array(line, dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)
        
        # 按 bbox 裁剪文本块
        x1, y1, x2, y2 = region['bbox']
        cropped = original_img[y1:y2, x1:x2]
        
        crop_filename = f"{image_name}_{idx}.jpg"
        crop_path = os.path.join(output_dir, crop_filename)
        cv2.imwrite(crop_path, cropped)
    
    # 将原图中的文本区域复制到白底图像
    result_img[mask == 255] = original_img[mask == 255]
    
    # 保存涂白结果
    output_full_path = os.path.join(os.getcwd(), f"{image_name}_text_only.jpg")
    cv2.imwrite(output_full_path, result_img)
    
    print(f"文本区域涂白结果已保存到: {output_full_path}")
    print(f"按 bbox 裁剪的文本块已保存到: {output_dir}")
    
    # 打印统计信息
    total_regions = data['stats']['total_regions']
    avg_confidence = data['stats']['avg_confidence']
    print(f"处理了 {total_regions} 个文本区域，平均置信度: {avg_confidence:.3f}")


if __name__ == "__main__":
    json_file = r"comic_text_detector\data\results\132_result.json"  # 请修改为实际的JSON文件路径
    
    if os.path.exists(json_file):
        extract_text_regions_from_json(json_file)
    else:
        print(f"JSON文件不存在: {json_file}")
