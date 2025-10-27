"""
右侧表单标签回填工具
用于将修改后的右侧标签JSON值回填到对应的URL中
"""

import os
import json
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import re

# 定义根目录
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def extract_url_parameter(url, param_name, default_value="", decode=False):
    """从URL中提取指定的参数值
    
    Args:
        url: 要提取参数的URL
        param_name: 要提取的参数名称
        default_value: 如果参数不存在时返回的默认值
        decode: 是否对提取的值进行URL解码
        
    Returns:
        提取的参数值或默认值
    """
    try:
        # 构建正则表达式匹配参数
        pattern = f'{param_name}=([^&]+)'
        match = re.search(pattern, url)
        if match:
            value = match.group(1)
            # 如果需要解码，则执行URL解码
            if decode:
                value = unquote(value)
            return value
    except Exception as e:
        print(f"提取URL参数'{param_name}'失败: {e}")
    # 如果无法提取，返回默认值
    return default_value

def extract_task_name(url):
    """从URL中提取taskName参数值"""
    return extract_url_parameter(url, 'taskName', "未命名任务", decode=True)

def extract_session_index(url):
    """从URL中提取sessionIndex参数值，如果没有则返回默认值1"""
    return extract_url_parameter(url, 'sessionIndex', "1")

def save_cookies(context, filename=os.path.join(ROOT_DIR, '.cache', 'cookies.json')):
    """保存cookies到文件"""
    cookies = context.cookies()
    with open(filename, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"Cookies已保存到 {filename}")

def load_cookies(context, filename=os.path.join(ROOT_DIR, '.cache', 'cookies.json')):
    """从文件加载cookies"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"已从 {filename} 加载cookies")
        return True
    return False

def fill_form_values(page, form_data):
    """填充表单值
    
    Args:
        page: Playwright页面对象
        form_data: 表单数据字典，键为标签文本，值为要填充的值
    """
    # 匹配class="query-item-right-annotation"的div元素
    annotation_divs = page.query_selector_all('div.query-item-right-annotation')
    
    filled_count = 0
    for div in annotation_divs:
        # 查找所有表单项
        form_items = div.query_selector_all('form.label-metrics-item')
        for form_item in form_items:
            # 查找表单项的标签
            label_elem = form_item.query_selector('label.mtd-form-item-label span[style*="color: rgb(22, 119, 255)"]')
            if label_elem:
                label_text = label_elem.text_content().strip()
                if label_text and label_text in form_data:
                    # 获取要填充的值
                    value_to_fill = form_data[label_text]
                    
                    # 尝试填充输入框
                    input_elem = form_item.query_selector('input.mtd-input')
                    if input_elem:
                        # 先清空输入框，然后填充新值
                        input_elem.fill("")
                        input_elem.fill(value_to_fill)
                        filled_count += 1
                        print(f"已填充 '{label_text}': '{value_to_fill}'")
                        continue
                    
                    # 尝试填充文本域
                    textarea_elem = form_item.query_selector('textarea.mtd-textarea')
                    if textarea_elem:
                        # 先清空文本域，然后填充新值
                        textarea_elem.fill("")
                        textarea_elem.fill(value_to_fill)
                        filled_count += 1
                        print(f"已填充 '{label_text}': '{value_to_fill}'")
    
    return filled_count

def fill_right_form_to_url(url, json_file_path, auto_submit=False, auto_close=True):
    """将修改后的右侧标签JSON值回填到对应的URL中
    
    Args:
        url: 目标URL
        json_file_path: 包含修改后表单数据的JSON文件路径
        auto_submit: 是否自动提交表单
        auto_close: 是否自动关闭浏览器
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 检查JSON文件是否存在
        if not os.path.exists(json_file_path):
            print(f"错误: JSON文件不存在: {json_file_path}")
            return False
        
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            form_data = json.load(f)
        
        if not form_data:
            print("错误: JSON文件为空")
            return False
        
        print(f"从 {json_file_path} 加载了 {len(form_data)} 个表单项")
        
        # 启动浏览器
        with sync_playwright() as p:
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            chrome_data_dir = os.path.join(ROOT_DIR, '.cache', 'chrome_data_fill')
            os.makedirs(chrome_data_dir, exist_ok=True)
            
            browser = p.chromium.launch_persistent_context(
                user_data_dir=chrome_data_dir,
                executable_path=chrome_path,
                headless=False,
                viewport={"width": 1280, "height": 720}
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            # 加载cookies
            load_cookies(browser)
            
            # 打开URL
            page.goto(url)
            time.sleep(3)  # 等待页面加载完全
            
            # 登录检测
            if "login" in page.url or page.query_selector('input[type="password"]'):
                print("检测到需要登录...")
                print("请在浏览器中完成登录，程序将继续执行...")
                time.sleep(10)
                save_cookies(browser)
            
            # 填充表单
            filled_count = fill_form_values(page, form_data)
            print(f"成功填充了 {filled_count} 个表单项")
            
            # 如果需要自动提交
            if auto_submit:
                # 查找提交按钮
                submit_button = page.query_selector('button[type="submit"], button:has-text("提交"), button:has-text("保存")')
                if submit_button:
                    submit_button.click()
                    print("已点击提交按钮")
                    time.sleep(2)  # 等待提交完成
                else:
                    print("未找到提交按钮，请手动提交")
            
            # 保存cookies
            save_cookies(browser)
            
            # 根据参数决定是否关闭浏览器
            if not auto_close:
                input("按回车键关闭浏览器...")
            
            browser.close()
            return True
            
    except Exception as e:
        print(f"填充表单失败: {e}")
        return False

def batch_fill_forms(base_url, start_index, end_index, task_name=None, auto_submit=False, auto_close=True):
    """批量填充表单
    
    Args:
        base_url: 基础URL（爬取时使用的URL，包含taskName等参数）
        start_index: 起始索引
        end_index: 结束索引
        task_name: 任务名称，如果为None则从URL中提取
        auto_submit: 是否自动提交表单
        auto_close: 是否自动关闭浏览器
    """
    # 如果URL中已包含sessionIndex参数，移除它以便后续替换
    if 'sessionIndex=' in base_url:
        # 移除现有的sessionIndex参数
        base_url = re.sub(r'sessionIndex=[^&]*&?', '', base_url)
        # 移除可能的尾部&符号
        if base_url.endswith('&'):
            base_url = base_url[:-1]
    
    # 确保URL末尾有合适的分隔符
    separator = '&' if '?' in base_url else '?'
    
    # 如果没有提供任务名称，从URL中提取
    if not task_name:
        task_name = extract_task_name(base_url)
    
    success_count = 0
    total_count = end_index - start_index + 1
    
    print(f"开始批量填充表单，任务名称: {task_name}")
    print(f"URL范围: {start_index} - {end_index}")
    
    for index in range(start_index, end_index + 1):
        # 构建包含当前sessionIndex的URL（使用爬取时的URL结构）
        url = f"{base_url}{separator}sessionIndex={index}"
        
        # 构建JSON文件路径（与crawler.py保存路径一致）
        json_file_path = os.path.join(ROOT_DIR, 'out', task_name, 'result', f"{index}_result.json")
        
        print(f"\n处理第 {index}/{total_count} 个URL: {url}")
        print(f"JSON文件路径: {json_file_path}")
        
        # 检查JSON文件是否存在
        if not os.path.exists(json_file_path):
            print(f"警告: JSON文件不存在，跳过此URL")
            continue
        
        # 填充表单
        success = fill_right_form_to_url(url, json_file_path, auto_submit, auto_close)
        if success:
            success_count += 1
            print(f"成功填充第 {index} 个URL")
        else:
            print(f"填充第 {index} 个URL失败")
        
        # 如果不是最后一个URL，稍作等待
        if index < end_index:
            time.sleep(2)
    
    print(f"\n批量填充完成！成功: {success_count}/{total_count}")
    return success_count

def load_url_from_file(task_name):
    """从任务目录中加载URL
    
    Args:
        task_name: 任务名称
        
    Returns:
        str: URL字符串，如果文件不存在则返回None
    """
    url_file = os.path.join(ROOT_DIR, 'out', task_name, 'result', 'url.txt')
    if os.path.exists(url_file):
        with open(url_file, 'r', encoding='utf-8') as f:
            url = f.read().strip()
        print(f"已从 {url_file} 加载URL: {url}")
        return url
    else:
        print(f"错误: URL文件不存在: {url_file}")
        return None

def batch_fill_from_saved_url(task_name, start_index, end_index, auto_submit=False, auto_close=True):
    """从保存的URL文件中进行批量填充
    
    Args:
        task_name: 任务名称
        start_index: 起始索引
        end_index: 结束索引
        auto_submit: 是否自动提交表单
        auto_close: 是否自动关闭浏览器
        
    Returns:
        int: 成功填充的数量
    """
    # 从任务目录中加载URL
    crawled_url = load_url_from_file(task_name)
    if not crawled_url:
        print(f"无法加载任务 '{task_name}' 的URL文件")
        return 0
    
    # 使用加载的URL进行批量填充
    return batch_fill_with_crawled_url(crawled_url, start_index, end_index, auto_submit, auto_close)

def batch_fill_with_crawled_url(crawled_url, start_index, end_index, auto_submit=False, auto_close=True):
    """使用爬取时的URL进行批量填充
    
    Args:
        crawled_url: 爬取时使用的URL，包含taskName等参数
        start_index: 起始索引
        end_index: 结束索引
        auto_submit: 是否自动提交表单
        auto_close: 是否自动关闭浏览器
        
    Returns:
        int: 成功填充的数量
    """
    # 解析URL，提取基础URL和任务名称
    from urllib.parse import urlparse, parse_qs
    
    parsed_url = urlparse(crawled_url)
    query_params = parse_qs(parsed_url.query)
    
    # 提取taskName
    task_name = query_params.get('taskName', [''])[0]
    if not task_name:
        print("错误: URL中未找到taskName参数")
        return 0
    
    # 构建基础URL（移除sessionIndex）
    base_query_params = {k: v for k, v in query_params.items() if k != 'sessionIndex'}
    from urllib.parse import urlencode
    new_query = urlencode(base_query_params, doseq=True)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"
    
    # 使用基础URL进行批量填充
    return batch_fill_forms(base_url, start_index, end_index, auto_submit, auto_close)

# 示例用法
if __name__ == "__main__":
    # 单个URL填充示例 (使用爬取时的URL结构)
    url = "http://example.com/form?sessionIndex=1"
    data_file = "out/task_name/result/1_result.json"
    
    # 填充单个表单
    fill_right_form_to_url(url, data_file, auto_submit=True)
    
    # 批量填充示例 (使用爬取时的URL结构)
    # base_url是爬取时使用的URL，不包含sessionIndex
    base_url = "http://example.com/form?taskName=example_task"
    batch_fill_forms(base_url, 1, 5, auto_submit=True)
    
    # 实际使用示例（使用爬取时的完整URL）
    crawled_url = "http://example.com/form?taskName=example_task&sessionIndex=1"
    batch_fill_with_crawled_url(crawled_url, 1, 5, auto_submit=True)
    
    # 新功能：从保存的URL文件中进行批量填充
    # 假设已经爬取了任务名为"example_task"的数据，并且URL已保存到url.txt
    batch_fill_from_saved_url("example_task", 1, 5, auto_submit=True)