import PIL.ImageGrab
import os
import json
import time
from wechat_ocr.ocr_manager import OcrManager, OCR_MAX_TASK_ID
import pyperclip
# 实现保存剪切板图片
def save_clipboard_pic(save_path):
    try:
        img = PIL.ImageGrab.grabclipboard()
        img.save(save_path)
        print("剪切板中的图片已经保存")
        return True
    except AttributeError:
        print("剪切板中不是图片")
        return False

def ocr_result_callback(img_path: str, results: dict):
    result_file = os.path.join("json", os.path.basename(img_path) + ".json")  # json\01.png.json，这里是包含文件夹名称
    print(f"识别成功，img_path: {img_path}, result_file: {result_file}")
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(results, ensure_ascii=False, indent=2))

def save_to_json(img_file):
    ocr_manager = OcrManager(wechat_dir)
    # 设置WeChatOcr目录
    ocr_manager.SetExePath(wechat_ocr_dir)
    # 设置微信所在路径
    ocr_manager.SetUsrLibDir(wechat_dir)
    # 设置ocr识别结果的回调函数
    ocr_manager.SetOcrResultCallback(ocr_result_callback)
    # 启动ocr服务
    ocr_manager.StartWeChatOCR()
    # TODO 识别图片
    ocr_manager.DoOCRTask(img_file)

    time.sleep(1)
    while ocr_manager.m_task_id.qsize() != OCR_MAX_TASK_ID:
        pass
    # 识别输出结果
    ocr_manager.KillWeChatOCR()

def save_text(json_file, save_file, mode=1):
    # 打开 JSON 文件
    with open(json_file, 'r', encoding='utf-8') as file:
        # 从文件中加载 JSON 数据
        data = json.load(file)
    # 换行保存
    if mode == 1:
        with open(save_file, 'w', encoding='utf-8') as f:
            # 提取每个对象的 text 字段
            for item in data['ocrResult']:
                print(item['text'])
                f.write(item['text'] + '\n')
    # 不换行保存
    if mode == 2:
        with open(save_file, 'w', encoding='utf-8') as f:
            # 提取每个对象的 text 字段
            for item in data['ocrResult']:
                print(item['text'])
                f.write(item['text'])

def txt_copy(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        # 读取文件内容
        file_content = file.read()
    # 将文件内容复制到剪贴板
    pyperclip.copy(file_content)
    print("已将文件内容复制到剪贴板。")

if __name__ == '__main__':
    # TODO 更改你电脑WeChatOCR.exe路径
    wechat_ocr_dir = r"C:\Users\Administrator\AppData\Roaming\Tencent\WeChat\XPlugin\Plugins\WeChatOCR\7079\extracted\WeChatOCR.exe"
    # TODO 更改你电脑mmmojo.dll所在路径
    wechat_dir = r"D:\WeChat\[3.9.12.45]"

    img_file = r"img\~~~ocr.png"
    if save_clipboard_pic(img_file):  # True表示剪切板图片已经保存，False表示剪切板根本不是图片
        file_name = os.path.basename(img_file)  # 使用 os.path.basename() 函数获取文件名
        json_file = os.path.join("json", file_name+".json")  # 通过上述操作将01.png变成json\01.png.json
        save_file = "text_save.txt"
        save_to_json(img_file)
        save_text(json_file, save_file, mode=1)
        txt_copy(save_file)