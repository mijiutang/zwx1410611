from playwright.sync_api import sync_playwright
import time
import json
import os
from bs4 import BeautifulSoup

def save_cookies(context, filename="cookies.json"):
    cookies = context.cookies()
    with open(filename, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"Cookies已保存到 {filename}")

def load_cookies(context, filename="cookies.json"):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"已从 {filename} 加载cookies")
        return True
    return False

def open_chrome_browser(
    url, 
    force_login=False, 
    save_html=False,
    save_target_contents=False  # 提取div内部内容
):
    try:
        with sync_playwright() as p:
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            browser = p.chromium.launch_persistent_context(
                user_data_dir="./chrome_data",
                executable_path=chrome_path,
                headless=False,
                viewport={"width": 1280, "height": 720}
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            if not force_login:
                load_cookies(browser)
            
            page.goto(url)
            time.sleep(3)  # 等待页面加载完全
            
            # 登录检测逻辑
            if force_login or "login" in page.url or page.query_selector('input[type="password"]'):
                print("检测到需要登录...")
                input("请在浏览器中完成登录，然后按回车键继续...")
                save_cookies(browser)
            
            # 保存完整HTML（可选）
            if save_html:
                html_content = page.content()
                with open("full_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("完整页面HTML已保存到 full_page.html")
            
            # 提取含“{现在时”的div内部内容（核心逻辑）
            if save_target_contents:
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 1. 获取所有属性匹配的div
                all_matched_divs = soup.find_all(
                    'div',
                    class_="hwt-highlights hwt-content",
                    attrs={"data-v-7794bacf": ""}
                )
                
                # 2. 过滤出含“{现在时”的div
                target_divs = [
                    div for div in all_matched_divs 
                    if "{现在时" in str(div)
                ]
                
                # 3. 提取并保存div内部内容（去掉外层div标签）
                if target_divs:
                    with open("target_div_contents.html", "w", encoding="utf-8") as f:
                        for i, div in enumerate(target_divs, 1):
                            inner_content = div.decode_contents()  # 保留HTML格式的内部内容
                            f.write(inner_content + "\n\n")
                    print(f"已保存 {len(target_divs)} 个div的内部内容到 target_div_contents.html")
                else:
                    print("未找到包含“{现在时”的目标div")
            
            print(f"已打开: {url}")
            input("按回车键关闭浏览器...")
            
            save_cookies(browser)
            browser.close()
            return True
            
    except Exception as e:
        print(f"打开浏览器失败: {e}")
        return False

if __name__ == "__main__":
    url = "https://aida-eval.sankuai.com/vue/model-training/labeling/data-labeling/task-labeling?id=16683&taskId=3954&type=3&taskName=%E3%80%90%E5%A4%96%E5%95%86%E5%9C%A8%E7%BA%BF%E3%80%911013-01%E7%9B%B4%E5%87%BA%E7%AC%AC%E5%9B%9B%E6%89%B9-%E5%91%A8%E5%BF%97%E5%8D%8E&sourcePath=%2Fmodel-training%2Flabeling%2Fdata-labeling%2Ftask-overview%2Fsession&sessionIndex=40"
    
    print("=== 打开系统Chrome（自动登录）===")
    success = open_chrome_browser(
        url, 
        force_login=False, 
        save_html=False, 
        save_target_contents=True  # 启用提取内部内容功能
    )
    
    if success:
        print("操作完成")
    else:
        print("操作失败")