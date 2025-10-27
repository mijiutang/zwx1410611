#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据回填脚本 - 将单个{session_index}_result.json的值按相同逻辑回填回URL
"""

import os
import json
import re
import sys
from urllib.parse import unquote, urlparse, parse_qs
from playwright.sync_api import sync_playwright
import time

def extract_session_index(filename):
    """从文件名中提取session_index"""
    match = re.match(r'(\d+)_result\.json', filename)
    return match.group(1) if match else None

def get_base_url_from_task(task_dir):
    """从任务目录的url.txt获取基础URL"""
    url_file = os.path.join(task_dir, "url.txt")
    if os.path.exists(url_file):
        with open(url_file, 'r', encoding='utf-8') as f:
            url = f.read().strip()
            # 移除sessionIndex参数，获取基础URL
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 'sessionIndex' in query_params:
                del query_params['sessionIndex']
            
            # 重建URL
            new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
            base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
            return base_url
    return None

def fill_form_data(page, data):
    """将数据填入表单"""
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
                if label_text and label_text in data:
                    value = data[label_text]
                    
                    # 首先检查是否是下拉框（mtd-select组件）
                    select_elem = form_item.query_selector('div.mtd-select')
                    if select_elem:
                        # 对于下拉框，需要先点击展开，然后选择选项
                        input_elem = select_elem.query_selector('input.mtd-input')
                        if input_elem:
                            # 点击下拉框展开选项
                            input_elem.click()
                            time.sleep(1)  # 增加等待时间，确保选项完全展开
                            
                            # 查找选项列表
                            # 尝试多种可能的选择器
                            options = page.query_selector_all('div[role="option"], .mtd-select-dropdown-item, .mtd-select-item')
                            if not options:
                                options = page.query_selector_all('div.mtd-dropdown-item, li.mtd-select-option')
                            if not options:
                                options = page.query_selector_all('.mtd-select-dropdown div[role="listitem"]')
                            if not options:
                                options = page.query_selector_all('.mtd-select-dropdown .mtd-option')
                            if not options:
                                options = page.query_selector_all('.mtd-select-dropdown .mtd-select-item')
                            if not options:
                                options = page.query_selector_all('.mtd-dropdown .mtd-option')
                            if not options:
                                # 尝试获取所有带有文本内容的div元素
                                all_divs = page.query_selector_all('div')
                                options = [div for div in all_divs if div.text_content().strip() in ['是', '否']]
                            
                            # 根据值选择对应的选项
                            option_found = False
                            if options:
                                # 如果值是"是"，选择第一个选项；如果是"否"，选择第二个选项
                                target_index = None
                                if value == "是" and len(options) > 0:
                                    target_index = 0
                                elif value == "否" and len(options) > 1:
                                    target_index = 1
                                
                                if target_index is not None:
                                    options[target_index].click()
                                    option_found = True
                                    filled_count += 1
                                    print(f"已选择下拉框 '{label_text}': '{value}' (选择第{target_index+1}个选项)")
                            
                            # 如果没有找到匹配的选项，尝试直接填入值
                            if not option_found:
                                input_elem.fill("")
                                input_elem.fill(value)
                                # 触发change事件
                                input_elem.evaluate('el => el.dispatchEvent(new Event("input", { bubbles: true }))')
                                input_elem.evaluate('el => el.dispatchEvent(new Event("change", { bubbles: true }))')
                                filled_count += 1
                                print(f"已填入下拉框 '{label_text}': '{value}' (未找到对应选项)")
                            
                            # 点击页面其他地方关闭下拉框
                            page.click('body')
                            time.sleep(0.5)
                            continue
                    
                    # 尝试填入普通输入框
                    input_elem = form_item.query_selector('input.mtd-input')
                    if input_elem:
                        # 先清空输入框
                        input_elem.fill("")
                        # 填入新值
                        input_elem.fill(value)
                        # 触发change事件
                        input_elem.evaluate('el => el.dispatchEvent(new Event("input", { bubbles: true }))')
                        input_elem.evaluate('el => el.dispatchEvent(new Event("change", { bubbles: true }))')
                        filled_count += 1
                        print(f"已填入 '{label_text}': '{value}'")
                        continue
                    
                    # 如果没有输入框，尝试填入文本域
                    textarea_elem = form_item.query_selector('textarea.mtd-textarea')
                    if textarea_elem:
                        # 先清空文本域
                        textarea_elem.fill("")
                        # 填入新值
                        textarea_elem.fill(value)
                        # 触发change事件
                        textarea_elem.evaluate('el => el.dispatchEvent(new Event("input", { bubbles: true }))')
                        textarea_elem.evaluate('el => el.dispatchEvent(new Event("change", { bubbles: true }))')
                        filled_count += 1
                        print(f"已填入 '{label_text}': '{value}'")
    
    return filled_count

def process_single_file(result_file_path, task_dir=None, headless=True):
    """处理单个结果文件"""
    print(f"\n处理结果文件: {result_file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(result_file_path):
        print(f"错误: 文件不存在: {result_file_path}")
        return False
    
    # 从文件名提取session_index
    filename = os.path.basename(result_file_path)
    session_index = extract_session_index(filename)
    if not session_index:
        print(f"错误: 无法从文件名 {filename} 提取session_index")
        return False
    
    # 如果没有提供任务目录，尝试从文件路径推断
    if not task_dir:
        # 假设文件路径是 .../任务目录/result/xxx_result.json
        parts = result_file_path.split(os.sep)
        if 'result' in parts:
            result_index = parts.index('result')
            if result_index > 0:
                task_dir = os.sep.join(parts[:result_index])
    
    if not task_dir:
        print("错误: 无法确定任务目录，请提供task_dir参数")
        return False
    
    # 获取基础URL
    base_url = get_base_url_from_task(task_dir)
    if not base_url:
        print(f"错误: 无法从 {task_dir}/url.txt 获取URL")
        return False
    
    # 构建完整URL
    full_url = f"{base_url}&sessionIndex={session_index}"
    print(f"目标URL: {full_url}")
    
    # 加载数据
    try:
        with open(result_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"已加载数据: {len(data)} 个字段")
    except Exception as e:
        print(f"错误: 无法加载 {result_file_path}: {e}")
        return False
    
    # 使用Playwright打开页面并填入数据
    # 定义根目录
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # 定义Chrome路径和数据目录
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    chrome_data_dir = os.path.join(ROOT_DIR, '.cache', 'chrome_data_filler')
    
    # 创建浏览器数据目录
    os.makedirs(chrome_data_dir, exist_ok=True)
    
    with sync_playwright() as p:
        try:
            # 使用持久化上下文，加载本地Chrome
            browser = p.chromium.launch_persistent_context(
                user_data_dir=chrome_data_dir,
                executable_path=chrome_path,
                headless=headless,
                viewport={"width": 1280, "height": 720}
            )
            
            # 加载cookie
            cookies_file = os.path.join(ROOT_DIR, '.cache', 'cookies.json')
            if os.path.exists(cookies_file):
                with open(cookies_file, 'r') as f:
                    cookies = json.load(f)
                browser.add_cookies(cookies)
                print(f"已从 {cookies_file} 加载cookies")
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            page.goto(full_url, wait_until="networkidle")
            print("页面加载完成")
            
            # 等待表单加载
            page.wait_for_selector('div.query-item-right-annotation', timeout=10000)
            print("表单已加载")
            
            # 填入数据
            filled_count = fill_form_data(page, data)
            print(f"成功填入 {filled_count} 个字段")
            
            # 等待一段时间确保数据已保存
            time.sleep(2)
            
            # 点击保存标注按钮
            try:
                save_button = page.query_selector('button.mtd-btn.mtd-btn-primary:has-text("保存标注")')
                if save_button:
                    save_button.click()
                    print("已点击保存标注按钮")
                    time.sleep(3)  # 等待保存完成
                else:
                    print("未找到保存标注按钮")
            except Exception as e:
                print(f"点击保存按钮时出错: {e}")
            
            # 保存cookie（可选）
            # save_cookies(browser)
            
            browser.close()
            return True
            
        except Exception as e:
            print(f"错误: 处理页面时出错: {e}")
            try:
                browser.close()
            except:
                pass
            return False
    
    print(f"\n文件 {result_file_path} 处理完成")
    return True

def main():
    """主函数"""
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("用法: python fill_form_data.py <结果文件路径> [任务目录路径] [--no-headless]")
        print("示例: python fill_form_data.py C:\\path\\to\\result\\1_result.json")
        print("示例: python fill_form_data.py C:\\path\\to\\result\\1_result.json C:\\path\\to\\task")
        print("使用 --no-headless 参数可以看到浏览器操作过程")
        return
    
    result_file_path = sys.argv[1]
    task_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    headless = "--no-headless" not in sys.argv
    
    # 处理单个文件
    success = process_single_file(result_file_path, task_dir, headless=headless)
    
    if success:
        print("\n处理完成!")
    else:
        print("\n处理过程中出现错误")

if __name__ == "__main__":
    main()