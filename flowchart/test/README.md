# 输入框值爬取脚本

本目录包含用于爬取网页输入框值的脚本。

## 脚本说明

### 1. extract_input_values.py
这是一个通用的输入框值爬取脚本，可以从网页URL或本地HTML文件中提取输入框值。

#### 功能特点：
- 支持从网页URL或本地HTML文件提取数据
- 提取高亮文本区域的值 (hwt-highlights)
- 提取信号项的值 (signal-item-value)
- 提取表单输入框的值
- 提取右侧表单标签的值
- 结果保存为JSON格式

#### 使用方法：
```bash
python extract_input_values.py
```

运行后按照提示选择输入源：
1. 网页URL
2. 本地HTML文件

### 2. extract_from_1html.py
这是一个简单的示例脚本，专门用于从1.html文件中提取输入框值。

#### 功能特点：
- 直接从1.html文件提取数据
- 显示详细的提取过程
- 结果保存为JSON格式

#### 使用方法：
```bash
python extract_from_1html.py
```

## 依赖安装

在使用脚本前，请确保安装以下依赖：

```bash
pip install playwright beautifulsoup4
playwright install
```

## 输出结果

脚本会将提取的结果保存为JSON文件，包含以下类型的数据：

1. 高亮文本区域的值
2. 信号项的值
3. 表单输入框的值
4. 右侧表单标签的值

## 注意事项

1. 对于网页URL提取，脚本会启动一个无头浏览器来加载页面
2. 提取结果会保存在脚本所在目录下
3. 如果输入框有值但在HTML中不显示，脚本会尝试从高亮文本区域提取值