from paddlex import create_pipeline
import os
import json
from pathlib import Path

# 1. 创建 OCR pipeline
pipeline = create_pipeline(pipeline="OCR")

# 2. 设置文件夹路径
image_folder = r"output_text_blocks"  # 修改为你的图片文件夹路径
output_json_file = "ocr_results.json"  # 输出的JSON文件名

# 支持的图片格式
supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

def process_images_in_folder(folder_path):
    """处理文件夹中的所有图片并返回结果字典"""
    results = {}
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"文件夹 {folder_path} 不存在！")
        return results
    
    # 获取文件夹中所有图片文件
    image_files = []
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in supported_formats:
                image_files.append(file)
    
    if not image_files:
        print(f"文件夹 {folder_path} 中没有找到支持的图片文件！")
        print(f"支持的格式: {', '.join(supported_formats)}")
        return results
    
    print(f"找到 {len(image_files)} 个图片文件，开始处理...")
    
    # 处理每个图片文件
    for i, image_file in enumerate(image_files, 1):
        image_path = os.path.join(folder_path, image_file)
        print(f"正在处理 ({i}/{len(image_files)}): {image_file}")
        
        try:
            # 执行OCR预测
            output = pipeline.predict(
                input=image_path,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
            )
            
            # 处理结果 - 从右至左拼接文本
            final_text = ""
            for res in output:
                # 使用字典方式访问属性
                texts = res['rec_texts']
                boxes = res['rec_boxes']
                
                # 创建文本和坐标的配对列表
                text_box_pairs = list(zip(texts, boxes))
                
                # 按照x坐标从大到小排序（从右至左）
                # boxes格式：[x_min, y_min, x_max, y_max]，使用x_min进行排序
                sorted_pairs = sorted(text_box_pairs, key=lambda pair: pair[1][0], reverse=True)
                
                # 提取排序后的文本并拼接
                sorted_texts = [pair[0] for pair in sorted_pairs]
                final_text = "".join(sorted_texts)
            
            # 将结果存储到字典中（图片名作为键，不包含扩展名）
            image_name = os.path.splitext(image_file)[0]
            results[image_name] = final_text
            
            print(f"  ✓ 处理完成: {len(final_text)} 个字符")
            
        except Exception as e:
            print(f"  ✗ 处理失败: {str(e)}")
            results[os.path.splitext(image_file)[0]] = ""
    
    return results

def save_results_to_json(results, output_file):
    """将结果保存为JSON文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")
        return True
    except Exception as e:
        print(f"保存JSON文件失败: {str(e)}")
        return False

# 主程序执行
if __name__ == "__main__":
    print("开始批量OCR处理...")
    
    # 处理文件夹中的所有图片
    ocr_results = process_images_in_folder(image_folder)
    
    if ocr_results:
        # 保存结果到JSON文件
        if save_results_to_json(ocr_results, output_json_file):
            print(f"\n处理完成！共处理 {len(ocr_results)} 个文件")
            
            # 显示部分结果预览
            print("\n结果预览:")
            for i, (image_name, text) in enumerate(ocr_results.items()):
                if i < 3:  # 只显示前3个结果
                    preview_text = text[:50] + "..." if len(text) > 50 else text
                    print(f"  {image_name}: {preview_text}")
            
            if len(ocr_results) > 3:
                print(f"  ... 还有 {len(ocr_results) - 3} 个结果")
        else:
            print("保存失败，但处理结果如下:")
            for image_name, text in ocr_results.items():
                print(f"{image_name}: {text}")
    else:
        print("没有处理任何文件！")