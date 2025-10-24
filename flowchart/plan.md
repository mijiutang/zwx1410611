# 智能表单联动功能开发计划书

## 1. 目标

为当前的表单填写系统增加智能联动能力。当用户修改某个“任务项”的值时，系统能根据预设的逻辑规则，自动更新或限制其他关联“任务项”的状态或内容。

**具体实现场景:**
- **场景一 (筛选选项)**: 当“任务项A”的值被设置为“某个值”时，“任务项B”的下拉框选项被自动筛选为指定的子集。
- **场景二 (禁用/启用)**: 当“任务项A”的值被设置为“某个值”时，“任务项B”变为灰色不可用状态。反之，当值不匹配时，恢复可用状态。

## 2. 核心思路

我们将采用**配置与逻辑分离**的设计模式，这是现代软件开发中的最佳实践。

- **规则配置文件 (YAML)**: 使用 YAML 文件 (`rules.yaml`) 来清晰、直观地定义所有联动规则。YAML 格式可读性强，且支持注释，非常适合由人工来阅读和维护。
- **规则执行引擎 (Python)**: 在现有的 PyQt6 代码中，编写一个“规则引擎”。这个引擎负责在程序运行时加载 `rules.yaml` 文件，并监听用户操作，一旦满足触发条件，就执行相应的规则。

**优势**:
- **易于维护**: 未来需要修改或增加联动规则时，只需修改 `rules.yaml` 文件，无需改动核心 Python 代码。
- **清晰直观**: 规则的定义和程序的执行逻辑分离，使得两部分都更加清晰，易于理解。

## 3. 配置文件设计 (`rules.yaml`)

我们将在 `flowchart` 目录下创建一个名为 `rules.yaml` 的文件，用于定义所有联动规则。

### 3.1. 文件结构

```yaml
# rules.yaml

# rules 是一个列表，可以包含多条独立的联动规则
rules:
  # --- 规则 1: 筛选下拉框选项 ---
  - source: 任务项A  # 触发联动的源字段
    value: "值1"     # 源字段需要满足的特定值
    target: 任务项B  # 被影响的目标字段
    action: filter_options # 要执行的动作：筛选选项
    # action 的参数：提供新的选项列表
    options:
      - "B的选项1"
      - "B的选项2"

  # --- 规则 2: 禁用字段 ---
  - source: 任务项A
    value: "值2"
    target: 任务项B
    action: disable # 要执行的动作：禁用

  # --- 规则 3: 启用字段 ---
  # 注意：为了实现“当A不为‘值2’时B恢复可用”，我们需要定义一个反向规则
  - source: 任务项A
    value: "值2"
    # not_value: true # (可选) 增加一个条件，表示当值不是 "值2" 时触发
    target: 任务项B
    action: enable # 要执行的动作：启用

  # --- 规则 4: 自动填充值 ---
  - source: 任务项C
    value: "某个值"
    target: 任务项D
    action: set_value # 要执行的动作：设置值
    # action 的参数：提供要设置的具体值
    new_value: "这是自动填充的值"
```

### 3.2. 字段解释

- `source`: (字符串) 触发联动的“任务项”名称。
- `value`: (字符串) `source` 项需要满足的值。
- `target`: (字符串) 被联动的“任务项”名称。
- `action`: (字符串) 需要执行的操作类型，主要包括：
    - `filter_options`: 筛选下拉框的选项。
    - `disable`: 禁用目标项，使其不可编辑。
    - `enable`: 启用目标项，使其恢复编辑。
    - `set_value`: 为目标项自动设置一个新值。
- `options`: (列表) `filter_options` 动作的参数，定义了新的下拉框选项。
- `new_value`: (字符串) `set_value` 动作的参数，定义了要填充的新值。

## 4. Python 代码实现步骤

所有代码修改将主要集中在 `flowchart/work/ui/key_value_editor_widget.py` 文件中。

### 4.1. 添加依赖

首先，需要为 Conda 环境安装 `PyYAML` 库。
```shell
pip install pyyaml
```

### 4.2. 修改 `KeyValueEditorWidget` 类

#### 4.2.1. 加载规则文件

在 `__init__` 方法中，增加加载 `rules.yaml` 的逻辑。

```python
# 在 __init__ 方法的开头
import yaml

class KeyValueEditorWidget(QWidget):
    def __init__(self, ...):
        super().__init__(...)
        # ... 其他初始化代码 ...
        self.rules = []
        self._load_rules() # 新增方法调用

    def _load_rules(self):
        # 假设 rules.yaml 与 flowchart 目录同级或在一个可预知的位置
        # 我们需要确定 rules.yaml 的确切路径
        rules_path = os.path.join(os.path.dirname(__file__), "..", "..", "rules.yaml") 
        if os.path.exists(rules_path):
            try:
                with open(rules_path, 'r', encoding='utf-8') as f:
                    self.rules = yaml.safe_load(f).get('rules', [])
            except Exception as e:
                QMessageBox.warning(self, "规则加载失败", f"无法加载或解析 rules.yaml: {e}")

```

#### 4.2.2. 创建规则执行引擎

我们需要一个新的方法来处理规则逻辑，并在每次数据变更后触发它。

```python
# 在 KeyValueEditorWidget 类中新增一个方法
def _apply_rules(self, changed_key, new_value):
    """
    根据变更的键和值，应用所有相关的联动规则。
    """
    for rule in self.rules:
        if rule.get('source') == changed_key and rule.get('value') == new_value:
            self._execute_action(rule)

def _execute_action(self, rule):
    """
    执行单条规则定义的动作。
    """
    target_key = rule.get('target')
    action = rule.get('action')

    # 1. 找到目标项所在的行
    target_row = -1
    for i in range(self.table_widget.rowCount()):
        if self.table_widget.item(i, 0).text() == target_key:
            target_row = i
            break
    
    if target_row == -1:
        return # 没有找到目标项，直接返回

    # 2. 获取目标单元格的控件
    value_widget = self.table_widget.cellWidget(target_row, 1) # QComboBox
    value_item = self.table_widget.item(target_row, 1) # QTableWidgetItem

    # 3. 根据 action 执行操作
    if action == 'disable':
        if value_widget:
            value_widget.setEnabled(False)
        if value_item:
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    elif action == 'enable':
        if value_widget:
            value_widget.setEnabled(True)
        if value_item:
            value_item.setFlags(value_item.flags() | Qt.ItemFlag.ItemIsEditable)

    elif action == 'filter_options' and isinstance(value_widget, QComboBox):
        new_options = rule.get('options', [])
        current_text = value_widget.currentText()
        value_widget.clear()
        value_widget.addItems(new_options)
        # 如果旧的值仍在新的选项中，则保留它
        if current_text in new_options:
            value_widget.setCurrentText(current_text)

    elif action == 'set_value':
        new_value = rule.get('new_value', '')
        if value_widget and isinstance(value_widget, QComboBox):
            value_widget.setCurrentText(new_value)
        elif value_item:
            value_item.setText(new_value)

```

#### 4.2.3. 触发规则引擎

修改 `save_changes` 方法，在每次保存变更后，调用规则引擎。

```python
# 在 save_changes 方法中
def save_changes(self):
    # ... (方法前半部分的现有代码) ...

    # 在 for 循环内部，当一个值被确认改变时
    if key_item:
        key = key_item.text()
        if key:
            updated_data[key] = value
            # !! 新增代码：触发规则检查 !!
            self._apply_rules(key, value) 
        else:
            # ...
    
    # ... (方法后半部分的现有代码) ...
```

## 5. 预期效果

- 当用户在表格中将“任务项A”的值修改为“值1”后，与“任务项B”对应的单元格将立刻从文本框或旧下拉框变为一个新的下拉框，且只包含 `["B的选项1", "B的选项2"]`。
- 当用户将“任务项A”的值修改为“值2”后，“任务项B”对应的单元格将立刻变为灰色，用户无法再对其进行编辑。

## 6. 总结

此计划书提供了一个完整、健壮且可扩展的方案，用于实现表单的智能联动功能。通过将规则与逻辑分离，我们不仅能完成当前的需求，也为未来更复杂的业务逻辑打下了坚实的基础。
