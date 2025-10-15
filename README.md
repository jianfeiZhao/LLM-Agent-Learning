# 旅游攻略小助手

基于Swarm框架的多Agent智能系统，采用分布式架构实现智能问答和旅游攻略生成。

## 🌟 特性

- **多Agent架构**: 包含Master、Planner、Executor、Writer四个专业Agent
- **大语言模型驱动**: 所有Agent都基于LLM进行智能决策和内容生成
- **动态Prompt管理**: 支持用户通过修改Prompt调整Agent的能力和行为
- **智能任务分解**: 自动分析查询复杂度，动态组建处理团队
- **DAG任务调度**: 使用有向无环图管理复杂任务的依赖关系
- **鲁棒性设计**: 支持工具失效时的自动切换和重试机制
- **Swarm协调**: 实现负载均衡和并发任务管理

## 🏗️ 系统架构

### Agent组件

1. **Master Agent（主控智能体）**
   - 分析用户查询复杂度
   - 动态组建处理团队
   - 协调其他Agent的工作

2. **Planner Agent（规划器）**
   - 将复杂查询分解为子任务
   - 构建DAG（有向无环图）
   - 分析任务依赖关系

3. **Executor Agent（执行器）**
   - 执行具体子任务
   - 调用外部工具（搜索、计算等）
   - 支持工具失效时的自动切换

4. **Writer Agent（生成器）**
   - 整合子任务结果
   - 生成连贯的最终答案
   - 过滤冗余和矛盾信息

### 工具组件

- **LLMClient**: 大语言模型客户端（支持OpenAI、模拟客户端）
- **PromptManager**: Prompt模板管理系统
- **SearchTool**: 搜索引擎接口
- **CalculatorTool**: 计算器工具
- **ComparisonTool**: 比较分析工具

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置你的API密钥：
```bash
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here

# LLM配置
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
```

3. 如果不配置OpenAI API密钥，系统将使用模拟客户端进行演示。

### 运行程序

#### 交互模式（默认）
```bash
python main.py
```

#### 演示模式
```bash
python main.py demo
```

#### 交互模式（显式指定）
```bash
python main.py interactive
```

#### Prompt管理工具
```bash
python prompt_manager.py
```

## 💡 使用示例

### 简单查询
```
💬 请输入您的问题: 汉武大帝的名字是什么？

🔄 正在处理: 汉武大帝的名字是什么？
⏳ 正在分析...
✅ 回答:
==================================================
## 汉武大帝（汉武帝）

**基本信息：**
- 姓名：刘彻
- 出生日期：公元前156年
- 逝世日期：公元前87年
- 在位时间：公元前141年 - 公元前87年（54年）
==================================================
```

### 复杂查询
```
💬 请输入您的问题: 汉武大帝和凯撒大帝谁更年长？

🔄 正在处理: 汉武大帝和凯撒大帝谁更年长？
⏳ 正在分析...
✅ 回答:
==================================================
## 汉武大帝 vs 凯撒大帝 年龄比较

**汉武大帝（汉武帝）**
- 出生：公元前156年
- 逝世：公元前87年
- 享年：69岁

**凯撒大帝（尤利乌斯·凯撒）**
- 出生：公元前100年7月12日
- 逝世：公元前44年3月15日
- 享年：56岁

**结论：**
汉武大帝比凯撒大帝年长56岁（公元前156年 vs 公元前100年），并且汉武大帝的寿命更长（69岁 vs 56岁）。
==================================================
```

### 旅游查询
```
💬 请输入您的问题: 北京有什么好玩的景点？

🔄 正在处理: 北京有什么好玩的景点？
⏳ 正在分析...
✅ 回答:
==================================================
## 北京旅游攻略

**推荐景点：**
- 故宫
- 天安门
- 长城
- 颐和园
- 天坛
- 北海公园

**特色美食：**
- 北京烤鸭
- 炸酱面
- 豆汁
- 焦圈
- 艾窝窝

**交通信息：**
地铁、公交、出租车都很方便

**温馨提示：**
- 建议提前预订酒店
- 注意天气变化，准备合适的衣物
- 热门景点建议避开节假日
==================================================
```

## 🔧 系统命令

- `status` - 查看系统状态和性能指标
- `help` - 显示帮助信息
- `prompt` - 进入Prompt管理工具
- `quit` / `exit` - 退出程序

## 🎛️ Prompt管理

系统支持动态修改Agent的Prompt模板，以调整Agent的行为和能力：

### 在交互模式中管理Prompt
1. 运行程序：`python main.py`
2. 输入 `prompt` 进入Prompt管理
3. 使用以下命令：
   - `list` - 列出所有Agent
   - `show <agent>` - 显示Agent的Prompt
   - `update <agent>` - 更新Agent的Prompt
   - `reset` - 重置为默认模板
   - `backup` - 备份当前配置
   - `restore` - 从备份恢复

### 独立Prompt管理工具
```bash
python prompt_manager.py
```

### Prompt配置文件
系统使用 `prompt_config.json` 文件存储Prompt模板，支持：
- 系统Prompt定制
- 用户Prompt模板调整
- 响应Schema定义
- 生成参数配置（温度、最大Token数等）

## 📊 性能监控

系统提供实时性能监控，包括：
- 总查询数
- 成功/失败查询数
- 活跃任务数
- 平均响应时间
- 系统运行时间
- 成功率统计

## 🛠️ 技术栈

- **Python 3.8+**
- **asyncio**: 异步编程
- **Pydantic**: 数据验证
- **NetworkX**: 图算法（DAG）
- **aiohttp**: 异步HTTP客户端

## 📁 项目结构

```
LLM-Agent-Learning/
├── agents/                 # Agent模块
│   ├── master_agent.py    # 主控智能体
│   ├── planner_agent.py   # 规划器
│   ├── executor_agent.py  # 执行器
│   └── writer_agent.py    # 生成器
├── tools/                 # 工具模块
│   ├── search_tool.py     # 搜索工具
│   ├── calculator_tool.py # 计算器工具
│   ├── comparison_tool.py # 比较工具
│   └── complexity_analyzer.py # 复杂度分析器
├── models.py              # 数据模型
├── config.py              # 配置管理
├── llm_client.py          # LLM客户端
├── prompt_templates.py    # Prompt模板系统
├── prompt_manager.py      # Prompt管理工具
├── prompt_config.json     # Prompt配置文件
├── swarm_coordinator.py   # Swarm协调器
├── main.py               # 主程序入口
├── requirements.txt      # 依赖文件
└── README.md            # 项目说明
```

## 🔮 未来规划

- [ ] 集成真实的搜索引擎API
- [ ] 添加更多旅游数据源
- [ ] 实现用户偏好学习
- [ ] 支持多语言查询
- [ ] 添加语音交互功能
- [ ] 实现移动端适配

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

---

**注意**: 这是一个演示项目，当前使用模拟数据。在生产环境中，请集成真实的API和数据源。
