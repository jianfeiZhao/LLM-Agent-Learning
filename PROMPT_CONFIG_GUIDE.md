# Prompt配置说明文档

## 概述

本文档详细说明了旅游攻略小助手系统中各个Agent的Prompt配置。系统采用基于JSON的配置文件来管理所有Agent的Prompt模板，支持动态修改和热更新。

## 配置文件

- **主配置文件**: `prompt_config.json`
- **配置管理模块**: `prompt_templates.py`
- **命令行管理工具**: `prompt_manager.py`

## Agent类型

系统包含4种类型的Agent，每种都有特定的职责和配置：

### 1. Master Agent (主控Agent)

**职责**：
- 分析用户查询的复杂度
- 决定处理策略（简单查询直接回答，复杂查询启动Planner）
- 作为系统的入口点

**配置参数**：
```json
{
  "system_prompt": "你是一个智能的Master Agent...",
  "user_prompt_template": "用户查询：{query}\n\n请分析这个查询的复杂度，并决定如何处理。",
  "response_schema": {
    "type": "object",
    "properties": {
      "complexity": {
        "type": "string",
        "enum": ["simple", "complex"],
        "description": "查询复杂度"
      },
      "reason": {
        "type": "string",
        "description": "复杂度判断理由"
      },
      "strategy": {
        "type": "string",
        "description": "处理策略"
      }
    },
    "required": ["complexity", "reason", "strategy"]
  },
  "temperature": 0.3,
  "max_tokens": 500
}
```

**参数说明**：
- `temperature`: 0.3 (较低，确保判断的一致性)
- `max_tokens`: 500 (适中的响应长度)

### 2. Planner Agent (规划Agent)

**职责**：
- 将复杂查询分解为多个子任务
- 分析任务间的依赖关系
- 构建任务执行的有向无环图(DAG)
- 制定详细的执行计划

**配置参数**：
```json
{
  "system_prompt": "你是一个专业的Planner Agent...",
  "user_prompt_template": "复杂查询：{query}\n\n请将这个查询分解为多个子任务，并分析任务依赖关系。",
  "response_schema": {
    "type": "object",
    "properties": {
      "tasks": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {"type": "string"},
            "type": {"type": "string", "enum": ["search", "calculate", "compare", "generate"]},
            "description": {"type": "string"},
            "priority": {"type": "integer", "minimum": 1, "maximum": 5}
          },
          "required": ["id", "type", "description", "priority"]
        }
      },
      "dependencies": {
        "type": "object",
        "description": "任务依赖关系，key为任务ID，value为依赖的任务ID列表"
      },
      "execution_order": {
        "type": "array",
        "items": {"type": "string"},
        "description": "任务执行顺序"
      }
    },
    "required": ["tasks", "dependencies", "execution_order"]
  },
  "temperature": 0.2,
  "max_tokens": 1500
}
```

**参数说明**：
- `temperature`: 0.2 (很低，确保规划的逻辑性)
- `max_tokens`: 1500 (较长的响应，包含详细规划)

### 3. Executor Agent (执行Agent)

**职责**：
- 执行具体的子任务
- 选择合适的工具（搜索、计算、比较等）
- 处理工具调用失败的情况
- 评估执行结果的质量

**配置参数**：
```json
{
  "system_prompt": "你是一个高效的Executor Agent...",
  "user_prompt_template": "任务描述：{task_description}\n任务类型：{task_type}\n\n请执行这个任务并返回结果。",
  "response_schema": {
    "type": "object",
    "properties": {
      "success": {"type": "boolean"},
      "result": {"type": "string"},
      "metadata": {
        "type": "object",
        "properties": {
          "tool_used": {"type": "string"},
          "execution_time": {"type": "number"},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        }
      },
      "error": {"type": "string", "description": "如果执行失败，提供错误信息"}
    },
    "required": ["success", "result"]
  },
  "temperature": 0.1,
  "max_tokens": 1000
}
```

**参数说明**：
- `temperature`: 0.1 (极低，确保执行的准确性)
- `max_tokens`: 1000 (适中的响应长度)

### 4. Writer Agent (写作Agent)

**职责**：
- 整合多个子任务的结果
- 过滤冗余和矛盾的信息
- 生成连贯、多视角的最终答案
- 确保答案的准确性和可读性

**配置参数**：
```json
{
  "system_prompt": "你是一个专业的Writer Agent...",
  "user_prompt_template": "用户查询：{query}\n子任务结果：{task_results}\n\n请整合这些结果，生成最终的答案。",
  "response_schema": {
    "type": "object",
    "properties": {
      "answer": {"type": "string", "description": "最终答案"},
      "sources": {
        "type": "array",
        "items": {"type": "string"},
        "description": "信息来源"
      },
      "confidence": {"type": "number", "minimum": 0, "maximum": 1},
      "metadata": {
        "type": "object",
        "properties": {
          "answer_type": {"type": "string"},
          "word_count": {"type": "integer"},
          "perspectives": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "required": ["answer", "sources", "confidence"]
  },
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**参数说明**：
- `temperature`: 0.7 (较高，确保答案的创造性和可读性)
- `max_tokens`: 2000 (较长的响应，包含详细答案)

## 配置管理

### 1. 通过代码管理

```python
from prompt_templates import get_prompt_manager, AgentType

# 获取Prompt管理器
prompt_manager = get_prompt_manager()

# 获取Agent模板
template = prompt_manager.get_template(AgentType.MASTER)

# 更新模板
new_template = PromptTemplate(
    system_prompt="新的系统Prompt",
    user_prompt_template="新的用户Prompt模板",
    temperature=0.5,
    max_tokens=800
)
prompt_manager.update_template(AgentType.MASTER, new_template)

# 保存到文件
prompt_manager.save_to_file()
```

### 2. 通过命令行管理

```bash
# 启动Prompt管理工具
python main.py prompt

# 或者直接运行
python prompt_manager.py
```

**可用命令**：
- `list` - 列出所有Agent
- `show <agent>` - 显示指定Agent的Prompt
- `update <agent>` - 更新指定Agent的Prompt
- `reset` - 重置为默认配置
- `backup <file>` - 备份当前配置
- `restore <file>` - 从备份恢复配置

### 3. 直接编辑配置文件

直接修改 `prompt_config.json` 文件，系统会在下次启动时自动加载新配置。

## 最佳实践

### 1. Temperature设置指南

- **Master Agent**: 0.3 (需要稳定的判断)
- **Planner Agent**: 0.2 (需要逻辑性强的规划)
- **Executor Agent**: 0.1 (需要准确的执行)
- **Writer Agent**: 0.7 (需要创造性的写作)

### 2. Max Tokens设置指南

- **Master Agent**: 500 (简短判断)
- **Planner Agent**: 1500 (详细规划)
- **Executor Agent**: 1000 (执行结果)
- **Writer Agent**: 2000 (完整答案)

### 3. Prompt编写建议

1. **明确职责**: 每个Agent的职责要清晰明确
2. **具体指令**: 给出具体的操作指令，避免模糊描述
3. **示例说明**: 在Prompt中包含示例，帮助模型理解
4. **错误处理**: 说明如何处理异常情况
5. **输出格式**: 明确指定输出格式和结构

### 4. 调试技巧

1. **逐步测试**: 先测试单个Agent，再测试整个流程
2. **日志记录**: 启用详细日志，观察Agent的决策过程
3. **参数调优**: 根据实际效果调整temperature和max_tokens
4. **A/B测试**: 对比不同Prompt配置的效果

## 故障排除

### 常见问题

1. **配置文件格式错误**
   - 检查JSON格式是否正确
   - 确保所有必需字段都存在

2. **Agent响应不符合预期**
   - 检查Prompt是否清晰明确
   - 调整temperature参数
   - 检查response_schema是否合理

3. **系统无法启动**
   - 检查配置文件是否存在
   - 验证所有依赖是否正确安装

### 调试命令

```bash
# 测试基本功能
python test_system.py

# 查看系统状态
python main.py status

# 进入交互模式测试
python main.py interactive
```

## 版本历史

- **v1.0**: 初始版本，支持基本的Prompt配置
- **v1.1**: 添加了命令行管理工具
- **v1.2**: 支持配置备份和恢复
- **v1.3**: 优化了响应Schema和参数设置

## 联系支持

如有问题或建议，请通过以下方式联系：
- 创建Issue
- 发送邮件
- 查看项目文档

---

*最后更新: 2024年12月*
