from paddlex import create_pipeline

# 1. 创建 OCR pipeline
pipeline = create_pipeline(pipeline="OCR")

# 2. 执行预测
output = pipeline.predict(
    input=r"text_fix\063.jpg",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
)

# 3. 处理结果 - 从右至左拼接文本
for res in output:
    # 使用字典方式访问属性
    texts = res['rec_texts']    # 改为字典访问方式
    boxes = res['rec_boxes']    # 改为字典访问方式
    
    # 创建文本和坐标的配对列表
    text_box_pairs = list(zip(texts, boxes))
    
    # 按照x坐标从大到小排序（从右至左）
    # boxes格式：[x_min, y_min, x_max, y_max]，使用x_min进行排序
    sorted_pairs = sorted(text_box_pairs, key=lambda pair: pair[1][0], reverse=True)
    
    # 提取排序后的文本并拼接
    sorted_texts = [pair[0] for pair in sorted_pairs]
    final_text = "".join(sorted_texts)
    
    print("从右至左拼接的文本:")
    print(final_text)
    
    # 如果需要查看排序过程，可以取消下面的注释
    print("\n排序详情:")
    for i, (text, box) in enumerate(sorted_pairs):
        print(f"第{i+1}个: '{text}' (x坐标: {box[0]})")