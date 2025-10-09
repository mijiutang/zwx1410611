import PIL.ImageGrab
import os
import json
import time
import logging
import pyperclip
import win32api
import win32con
from wechat_ocr.ocr_manager import OcrManager, OCR_MAX_TASK_ID

# 日志配置
logging.basicConfig(
    filename='wechat_ocr.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def save_clipboard_pic(save_path):
    try:
        img = PIL.ImageGrab.grabclipboard()
        if img:
            img.save(save_path)
            logging.info("剪切板中的图片已经保存")
            return True
        else:
            logging.warning("剪切板中不包含图片")
            return False
    except Exception as e:
        logging.exception("保存剪切板图片失败")
        return False

def ocr_result_callback(img_path: str, results: dict):
    try:
        result_file = os.path.join("json", os.path.basename(img_path) + ".json")
        logging.info(f"识别成功，img_path: {img_path}, result_file: {result_file}")
        os.makedirs("json", exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(results, ensure_ascii=False, indent=2))
    except Exception as e:
        logging.exception("OCR结果回调处理失败")

def save_text(json_file, save_file, mode=1):
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        with open(save_file, 'w', encoding='utf-8') as f:
            for item in data['ocrResult']:
                f.write(item['text'] + ('\n' if mode == 1 else ''))
        logging.info(f"文本已保存到 {save_file}")
    except Exception as e:
        logging.exception("保存文本失败")

def txt_copy(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            pyperclip.copy(file.read())
        logging.info("已将文件内容复制到剪贴板。")
    except Exception as e:
        logging.exception("复制文本到剪贴板失败")

if __name__ == '__main__':
    try:
        wechat_ocr_dir = r"C:\Users\Administrator\AppData\Roaming\Tencent\WeChat\XPlugin\Plugins\WeChatOCR\7079\extracted\WeChatOCR.exe"
        wechat_dir = r"D:\WeChat\[3.9.12.51]"

        if not os.path.exists(wechat_ocr_dir) or not os.path.exists(wechat_dir):
            logging.error("配置路径无效，请检查wechat_ocr_dir和wechat_dir")
            raise FileNotFoundError("WeChatOCR或微信路径无效")

        ocr_manager = OcrManager(wechat_dir)
        ocr_manager.SetExePath(wechat_ocr_dir)
        ocr_manager.SetUsrLibDir(wechat_dir)
        ocr_manager.SetOcrResultCallback(ocr_result_callback)
        ocr_manager.StartWeChatOCR()
        logging.info("OCR 服务已启动")

        print("按下 Ctrl+C 实现微信OCR识别图片并复制到剪切板")
        print("按下 Esc 退出程序")

        while True:
            if win32api.GetAsyncKeyState(ord('C')) and win32api.GetAsyncKeyState(win32con.VK_CONTROL):
                logging.info("检测到 Ctrl+C")
                img_file = r"img\~~~ocr.png"
                os.makedirs("img", exist_ok=True)
                if save_clipboard_pic(img_file):
                    file_name = os.path.basename(img_file)
                    json_file = os.path.join("json", file_name + ".json")
                    save_file = "text_save.txt"
                    ocr_manager.DoOCRTask(img_file)
                    logging.info("OCR识别任务已提交")
                    time.sleep(1)
                    while ocr_manager.m_task_id.qsize() != OCR_MAX_TASK_ID:
                        pass
                    save_text(json_file, save_file, mode=1)
                    txt_copy(save_file)
                time.sleep(0.5)

            if win32api.GetAsyncKeyState(win32con.VK_ESCAPE):
                logging.info("检测到 Esc，准备退出")
                break

            time.sleep(0.1)

    except Exception as e:
        logging.exception("程序发生异常")

    finally:
        try:
            ocr_manager.KillWeChatOCR()
            logging.info("OCR 服务已关闭")
        except:
            pass
        logging.info("程序退出")
