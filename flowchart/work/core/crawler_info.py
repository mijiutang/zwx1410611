from playwright.sync_api import sync_playwright
import time
import json
import os
from bs4 import BeautifulSoup

class SignalExtractor:
    def __init__(self, page):
        self.page = page

    def extract_signal_data(self):
        selector = 'div.hwt-highlights.hwt-content'
        div_element = self.page.query_selector(selector)

        if div_element:
            text_content = div_element.text_content()
            filtered_lines = [line for line in text_content.splitlines() if line.strip().startswith("{现在时间")]
            return "\n".join(filtered_lines)
        else:
            return "Error: Could not find the specified div element."

def save_cookies(context, filename=r"C:\Users\1\Desktop\workfast\zwx1410611\flowchart\work\core\cookies.json", log_callback=None):
    """保存cookies到文件"""
    cookies = context.cookies()
    with open(filename, 'w') as f:
        json.dump(cookies, f, indent=2)
    if log_callback:
        log_callback(f"Cookies已保存到 {filename}")
    else:
        print(f"Cookies已保存到 {filename}")

def load_cookies(context, filename=r"C:\Users\1\Desktop\workfast\zwx1410611\flowchart\work\core\cookies.json", log_callback=None):
    """从文件加载cookies"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        if log_callback:
            log_callback(f"已从 {filename} 加载cookies")
        else:
            print(f"已从 {filename} 加载cookies")
        return True
    return False

def open_chrome_browser(url, force_login=False, log_callback=None, cookie_string=None):
    """使用系统Chrome打开浏览器，支持cookies自动登录和设置自定义cookie"""
    p = sync_playwright().start()
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
        if log_callback:
            log_callback("启动系统Chrome...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./chrome_data",
            executable_path=chrome_path,
            headless=False,
            viewport={"width": 1280, "height": 720}
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        if not force_login:
            load_cookies(browser, log_callback=log_callback)

        # Set custom cookies if provided
        if cookie_string:
            try:
                # Assuming cookie_string is in the format "name=value; name2=value2"
                # Playwright expects a list of dictionaries for add_cookies
                cookies_to_set = []
                for cookie_pair in cookie_string.split(';'):
                    if '=' in cookie_pair:
                        name, value = cookie_pair.split('=', 1)
                        cookies_to_set.append({'name': name.strip(), 'value': value.strip(), 'url': url})
                if cookies_to_set:
                    page.context.add_cookies(cookies_to_set)
                    if log_callback:
                        log_callback(f"已设置自定义Cookie: {cookie_string}")
            except Exception as e:
                if log_callback:
                    log_callback(f"设置自定义Cookie失败: {e}")

        page.goto(url)
        time.sleep(3)  # 等待页面加载完全
        
        if force_login or "login" in page.url or page.query_selector('input[type="password"]'):
            if log_callback:
                log_callback("检测到需要登录...")
            input("请在浏览器中完成登录，然后按回车键继续...")
            save_cookies(browser, log_callback=log_callback)
            if log_callback:
                log_callback("登录状态已保存")
        
        if log_callback:
            log_callback(f"已打开: {url}")
        return page, browser, p
            
    except Exception as e:
        if log_callback:
            log_callback(f"打开浏览器失败: {e}")
        else:
            print(f"打开浏览器失败: {e}")
        return None, None, None

if __name__ == "__main__":
    url = "https://aida-eval.sankuai.com/vue/model-training/labeling/data-labeling/task-labeling?id=16683&taskId=3954&type=3&taskName=%E3%80%90%E5%A4%96%E5%95%86%E5%9C%A8%E7%BA%BF%E3%80%911013-01%E7%9B%B4%E5%87%BA%E7%AC%AC%E5%9B%9B%E6%89%B9-%E5%91%A8%E5%BF%97%E5%8D%8E&sourcePath=%2Fmodel-training%2Flabeling%2Fdata-labeling%2Ftask-overview%2Fsession&sessionIndex=40"
    
    print("=== 打开系统Chrome（自动登录）并提取信号数据 ===")
    
    def console_log(message):
        print(message)

    page, browser, p = open_chrome_browser(url, force_login=False, log_callback=console_log)
    
    if page:
        extractor = SignalExtractor(page)
        signal_data = extractor.extract_signal_data()
        console_log("\n--- 提取到的信号数据 ---")
        console_log(signal_data)
        
        input("\n按回车键关闭浏览器...")
        save_cookies(browser, log_callback=console_log)
        browser.close()
        p.stop()
        console_log("浏览器已关闭")
    else:
        console_log("操作失败")