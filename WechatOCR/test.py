import PIL.ImageGrab
import os
import json
import time
import logging
import pyperclip
import win32api
import win32con
import traceback
from wechat_ocr.ocr_manager import OcrManager, OCR_MAX_TASK_ID

# 日志配置
logging.basicConfig(
    filename='wechat_ocr.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def save_clipboard_pic(save_path):
    """保存剪切板中的图片并检查有效性"""
    try:
        img = PIL.ImageGrab.grabclipboard()
        if img is None:
            logging.warning("剪切板中不包含图片或图片格式不支持")
            return False
        
        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))
        
        img.save(save_path)
        if not os.path.exists(save_path):
            logging.error(f"图片保存失败: {save_path}")
            return False
            
        logging.info(f"图片已保存到: {save_path}")
        return True
    except Exception as e:
        logging.error(f"保存剪切板图片失败: {str(e)}\n{traceback.format_exc()}")
        return False

def ocr_result_callback(img_path: str, results: dict):
    """OCR结果回调函数，增加数据有效性检查"""
    try:
        if not results or 'ocrResult' not in results:
            logging.error(f"无效的OCR结果: {results}")
            return
            
        result_dir = "json"
        os.makedirs(result_dir, exist_ok=True)
        result_file = os.path.join(result_dir, os.path.basename(img_path) + ".json")
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        logging.info(f"OCR结果已保存: {result_file}")
    except Exception as e:
        logging.error(f"OCR结果处理失败: {str(e)}\n{traceback.format_exc()}")

def save_text(json_file, save_file, mode=1):
    """保存文本内容，增加文件存在性检查"""
    try:
        if not os.path.exists(json_file):
            logging.error(f"JSON文件不存在: {json_file}")
            return False
            
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        if not data or 'ocrResult' not in data:
            logging.error(f"无效的JSON数据: {data}")
            return False
            
        with open(save_file, 'w', encoding='utf-8') as f:
            for item in data['ocrResult']:
                if 'text' in item:
                    f.write(item['text'] + ('\n' if mode == 1 else ''))
                    
        logging.info(f"文本已保存到: {save_file}")
        return True
    except Exception as e:
        logging.error(f"保存文本失败: {str(e)}\n{traceback.format_exc()}")
        return False

def txt_copy(file_path):
    """复制文本到剪贴板，增加文件检查"""
    try:
        if not os.path.exists(file_path):
            logging.error(f"文本文件不存在: {file_path}")
            return False
            
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            if not content:
                logging.warning("文本文件内容为空")
                return False
                
            pyperclip.copy(content)
            
        logging.info("文本已复制到剪贴板")
        return True
    except Exception as e:
        logging.error(f"复制文本失败: {str(e)}\n{traceback.format_exc()}")
        return False

def check_wechat_paths(wechat_ocr_dir, wechat_dir):
    """检查微信相关路径有效性"""
    paths_valid = True
    if not os.path.exists(wechat_ocr_dir):
        logging.error(f"WeChatOCR路径不存在: {wechat_ocr_dir}")
        paths_valid = False
        
    if not os.path.exists(wechat_dir):
        logging.error(f"微信安装路径不存在: {wechat_dir}")
        paths_valid = False
        
    return paths_valid

def main():
    try:
        # 配置路径
        wechat_ocr_dir = r"C:\Users\Administrator\AppData\Roaming\Tencent\WeChat\XPlugin\Plugins\WeChatOCR\7079\extracted\WeChatOCR.exe"
        wechat_dir = r"D:\WeChat\[3.9.12.51]"
        
        # 检查路径有效性
        if not check_wechat_paths(wechat_ocr_dir, wechat_dir):
            raise FileNotFoundError("WeChatOCR或微信路径无效")
        
        # 初始化OCR管理器
        ocr_manager = OcrManager(wechat_dir)
        ocr_manager.SetExePath(wechat_ocr_dir)
        ocr_manager.SetUsrLibDir(wechat_dir)
        ocr_manager.SetOcrResultCallback(ocr_result_callback)
        
        # 启动OCR服务
        if not ocr_manager.StartWeChatOCR():
            raise RuntimeError("启动WeChatOCR失败")
        logging.info("OCR服务启动成功")
        
        print("按下 Ctrl+C 实现微信OCR识别图片并复制到剪切板")
        print("按下 Esc 退出程序")

        while True:
            try:
                # 检测Ctrl+C
                if win32api.GetAsyncKeyState(ord('C')) < 0 and win32api.GetAsyncKeyState(win32con.VK_CONTROL) < 0:
                    logging.info("检测到 Ctrl+C 快捷键")
                    img_file = r"img\~~~ocr.png"
                    
                    if save_clipboard_pic(img_file):
                        json_file = os.path.join("json", os.path.basename(img_file) + ".json")
                        save_file = "text_save.txt"
                        
                        # 执行OCR任务
                        if not ocr_manager.DoOCRTask(img_file):
                            logging.error("OCR任务提交失败")
                            continue
                            
                        logging.info("OCR任务已提交，等待结果...")
                        
                        # 等待任务完成（增加超时机制）
                        start_time = time.time()
                        while ocr_manager.m_task_id.qsize() != OCR_MAX_TASK_ID:
                            if time.time() - start_time > 10:  # 10秒超时
                                logging.error("OCR任务处理超时")
                                break
                            time.sleep(0.1)
                            
                        # 处理结果
                        if save_text(json_file, save_file, mode=1):
                            txt_copy(save_file)
                            
                    time.sleep(0.5)  # 防止重复触发
                
                # 检测Esc键
                if win32api.GetAsyncKeyState(win32con.VK_ESCAPE) < 0:
                    logging.info("检测到 Esc 键，准备退出")
                    break
                    
                time.sleep(0.1)
                
            except Exception as e:
                logging.error(f"主循环发生错误: {str(e)}\n{traceback.format_exc()}")
                time.sleep(1)  # 防止错误循环占用CPU

    except Exception as e:
        logging.critical(f"程序发生严重错误: {str(e)}\n{traceback.format_exc()}")
        print(f"程序出错: {str(e)}")

    finally:
        try:
            if 'ocr_manager' in locals():
                ocr_manager.KillWeChatOCR()
                logging.info("OCR服务已关闭")
        except Exception as e:
            logging.error(f"关闭OCR服务失败: {str(e)}")
            
        logging.info("程序退出")

if __name__ == '__main__':
    main()