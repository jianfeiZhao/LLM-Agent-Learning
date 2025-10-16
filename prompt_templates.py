"""
简化版Prompt模板系统
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
    
    def load_default_templates(self):
        """加载默认模板"""
        self.templates = {
            AgentType.MASTER: PromptTemplate(
                system_prompt="你是一个智能的Master Agent，负责分析用户查询的复杂度并决定处理策略。",
                user_prompt_template="用户查询：{query}\n\n请分析这个查询的复杂度，并决定如何处理。"
            ),
            
            AgentType.PLANNER: PromptTemplate(
                system_prompt="你是一个专业的Planner Agent，负责将复杂查询分解为多个子任务并构建执行计划。",
                user_prompt_template="复杂查询：{query}\n\n请将这个查询分解为多个子任务，并分析任务依赖关系。"
            ),
            
            AgentType.EXECUTOR: PromptTemplate(
                system_prompt="你是一个高效的Executor Agent，负责执行具体的子任务。",
                user_prompt_template="任务描述：{task_description}\n任务类型：{task_type}\n\n请执行这个任务并返回结果。"
            ),
            
            AgentType.WRITER: PromptTemplate(
                system_prompt="你是一个专业的Writer Agent，负责整合多个任务的结果并生成最终的答案。",
                user_prompt_template="用户查询：{query}\n子任务结果：{task_results}\n\n请整合这些结果，生成最终的答案。"
            )
        }
    
    def get_template(self, agent_type: AgentType) -> PromptTemplate:
        """获取Agent的Prompt模板"""
        return self.templates.get(agent_type)
    
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
        return None
    
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
