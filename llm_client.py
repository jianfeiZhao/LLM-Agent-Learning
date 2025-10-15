"""
LLM客户端
支持多种大语言模型的统一接口
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import openai
from config import settings

class LLMClient(ABC):
    """LLM客户端抽象基类"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        pass
    
    @abstractmethod
    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """生成结构化响应"""
        pass

class OpenAIClient(LLMClient):
    """OpenAI客户端"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
                top_p=kwargs.get("top_p", 1.0),
                frequency_penalty=kwargs.get("frequency_penalty", 0.0),
                presence_penalty=kwargs.get("presence_penalty", 0.0)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {str(e)}")
    
    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """生成结构化响应"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的AI助手，请严格按照JSON格式返回结果。"},
                    {"role": "user", "content": f"{prompt}\n\n请返回JSON格式的结果，符合以下schema：\n{json.dumps(schema, ensure_ascii=False, indent=2)}"}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            # 尝试解析JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果解析失败，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise Exception("无法解析JSON响应")
        except Exception as e:
            raise Exception(f"OpenAI结构化响应生成失败: {str(e)}")

class MockLLMClient(LLMClient):
    """模拟LLM客户端（用于测试）"""
    
    def __init__(self):
        self.responses = {
            "complexity_analysis": "complex",
            "task_planning": "需要分解为多个子任务",
            "execution": "执行结果",
            "writing": "生成的答案内容"
        }
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成模拟响应"""
        await asyncio.sleep(0.5)  # 模拟网络延迟
        
        # 根据prompt内容返回不同的模拟响应
        if "复杂度" in prompt or "complexity" in prompt.lower():
            return "complex"
        elif "规划" in prompt or "planning" in prompt.lower():
            return "需要分解为多个子任务"
        elif "执行" in prompt or "execution" in prompt.lower():
            return "执行结果"
        elif "生成" in prompt or "writing" in prompt.lower():
            return "生成的答案内容"
        else:
            return "这是一个模拟的LLM响应"
    
    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟结构化响应"""
        await asyncio.sleep(0.5)
        
        # 返回符合schema的模拟数据
        if "complexity" in schema:
            return {"complexity": "complex", "reason": "查询包含多个子问题"}
        elif "tasks" in schema:
            return {
                "tasks": [
                    {"id": "task1", "type": "search", "description": "搜索相关信息"},
                    {"id": "task2", "type": "calculate", "description": "执行计算"}
                ],
                "dependencies": {"task2": ["task1"]}
            }
        else:
            return {"result": "模拟结构化响应"}

class LLMClientFactory:
    """LLM客户端工厂"""
    
    @staticmethod
    def create_client(provider: str = "openai", **kwargs) -> LLMClient:
        """创建LLM客户端"""
        if provider == "openai":
            api_key = kwargs.get("api_key") or settings.openai_api_key
            if not api_key:
                raise Exception("OpenAI API密钥未配置")
            return OpenAIClient(api_key=api_key, model=kwargs.get("model", "gpt-3.5-turbo"))
        elif provider == "mock":
            return MockLLMClient()
        else:
            raise Exception(f"不支持的LLM提供商: {provider}")

# 全局LLM客户端实例
llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    """获取全局LLM客户端"""
    global llm_client
    if llm_client is None:
        # 默认使用模拟客户端，用户可以通过环境变量配置
        provider = settings.openai_api_key and "openai" or "mock"
        llm_client = LLMClientFactory.create_client(provider=provider)
    return llm_client

def set_llm_client(client: LLMClient):
    """设置全局LLM客户端"""
    global llm_client
    llm_client = client
