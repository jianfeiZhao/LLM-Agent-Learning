"""
Prompt模板系统
支持动态加载和修改Agent的Prompt模板
"""
import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AgentType(str, Enum):
    """Agent类型枚举"""
    MASTER = "master"
    PLANNER = "planner"
    EXECUTOR = "executor"
    WRITER = "writer"

@dataclass
class PromptTemplate:
    """Prompt模板"""
    system_prompt: str
    user_prompt_template: str
    response_schema: Optional[Dict[str, Any]] = None
    temperature: float = 0.7
    max_tokens: int = 1000

class PromptManager:
    """Prompt管理器"""
    
    def __init__(self, config_file: str = "prompt_config.json"):
        self.config_file = config_file
        self.templates: Dict[AgentType, PromptTemplate] = {}
        self.load_default_templates()
        self.load_from_file()
    
    def load_default_templates(self):
        """加载默认模板"""
        self.templates = {
            AgentType.MASTER: PromptTemplate(
                system_prompt="""你是一个智能的Master Agent，负责分析用户查询的复杂度并决定处理策略。

你的职责：
1. 分析用户查询的复杂度（简单/复杂）
2. 对于简单查询，直接生成答案
3. 对于复杂查询，启动Planner进行任务分解

请根据用户查询的内容，判断其复杂度并给出相应的处理建议。""",
                user_prompt_template="用户查询：{query}\n\n请分析这个查询的复杂度，并决定如何处理。",
                response_schema={
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
                }
            ),
            
            AgentType.PLANNER: PromptTemplate(
                system_prompt="""你是一个专业的Planner Agent，负责将复杂查询分解为多个子任务并构建执行计划。

你的职责：
1. 分析复杂查询，识别需要的信息
2. 将查询分解为多个可执行的子任务
3. 分析任务之间的依赖关系
4. 构建任务执行的有向无环图(DAG)

请根据用户查询，制定详细的执行计划。""",
                user_prompt_template="复杂查询：{query}\n\n请将这个查询分解为多个子任务，并分析任务依赖关系。",
                response_schema={
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
                }
            ),
            
            AgentType.EXECUTOR: PromptTemplate(
                system_prompt="""你是一个高效的Executor Agent，负责执行具体的子任务。

你的职责：
1. 根据任务类型选择合适的工具
2. 执行搜索、计算、比较等操作
3. 处理工具调用失败的情况
4. 评估执行结果的质量

请根据任务描述，执行相应的操作并返回结果。""",
                user_prompt_template="任务描述：{task_description}\n任务类型：{task_type}\n\n请执行这个任务并返回结果。",
                response_schema={
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
                }
            ),
            
            AgentType.WRITER: PromptTemplate(
                system_prompt="""你是一个专业的Writer Agent，负责整合多个任务的结果并生成最终的答案。

你的职责：
1. 整合多个子任务的结果
2. 过滤冗余和矛盾的信息
3. 生成连贯、多视角的最终答案
4. 确保答案的准确性和可读性

请根据子任务的结果，生成高质量的最终答案。""",
                user_prompt_template="用户查询：{query}\n子任务结果：{task_results}\n\n请整合这些结果，生成最终的答案。",
                response_schema={
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
                    },
                    "required": ["answer", "sources", "confidence"]
                }
            }
        )
    
    def load_from_file(self):
        """从文件加载模板"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                for agent_type_str, template_config in config.items():
                    agent_type = AgentType(agent_type_str)
                    self.templates[agent_type] = PromptTemplate(
                        system_prompt=template_config["system_prompt"],
                        user_prompt_template=template_config["user_prompt_template"],
                        response_schema=template_config.get("response_schema"),
                        temperature=template_config.get("temperature", 0.7),
                        max_tokens=template_config.get("max_tokens", 1000)
                    )
                print(f"✅ 已从 {self.config_file} 加载Prompt模板")
            except Exception as e:
                print(f"⚠️ 加载Prompt配置文件失败: {str(e)}")
    
    def save_to_file(self):
        """保存模板到文件"""
        try:
            config = {}
            for agent_type, template in self.templates.items():
                config[agent_type.value] = {
                    "system_prompt": template.system_prompt,
                    "user_prompt_template": template.user_prompt_template,
                    "response_schema": template.response_schema,
                    "temperature": template.temperature,
                    "max_tokens": template.max_tokens
                }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存Prompt模板到 {self.config_file}")
        except Exception as e:
            print(f"❌ 保存Prompt配置文件失败: {str(e)}")
    
    def get_template(self, agent_type: AgentType) -> PromptTemplate:
        """获取Agent的Prompt模板"""
        return self.templates.get(agent_type)
    
    def update_template(self, agent_type: AgentType, template: PromptTemplate):
        """更新Agent的Prompt模板"""
        self.templates[agent_type] = template
        print(f"✅ 已更新 {agent_type.value} Agent的Prompt模板")
    
    def format_prompt(self, agent_type: AgentType, **kwargs) -> tuple[str, str]:
        """格式化Prompt"""
        template = self.get_template(agent_type)
        if not template:
            raise Exception(f"未找到 {agent_type.value} Agent的模板")
        
        system_prompt = template.system_prompt
        user_prompt = template.user_prompt_template.format(**kwargs)
        
        return system_prompt, user_prompt
    
    def get_response_schema(self, agent_type: AgentType) -> Optional[Dict[str, Any]]:
        """获取响应Schema"""
        template = self.get_template(agent_type)
        return template.response_schema if template else None
    
    def get_generation_params(self, agent_type: AgentType) -> Dict[str, Any]:
        """获取生成参数"""
        template = self.get_template(agent_type)
        if not template:
            return {"temperature": 0.7, "max_tokens": 1000}
        
        return {
            "temperature": template.temperature,
            "max_tokens": template.max_tokens
        }

# 全局Prompt管理器实例
prompt_manager = PromptManager()

def get_prompt_manager() -> PromptManager:
    """获取全局Prompt管理器"""
    return prompt_manager