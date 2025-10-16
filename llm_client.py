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
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", base_url: Optional[str] = None):
        # 允许自定义 base_url，未提供则使用默认配置
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url or settings.openai_base_url)
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
            # 检查内容是否为空
            if not content or not content.strip():
                raise Exception("LLM返回空响应")
            
            # 尝试解析JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON解析失败: {str(e)}")
                print(f"📝 原始内容: {content[:200]}...")
                # 如果解析失败，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise Exception("无法解析提取的JSON部分")
                else:
                    raise Exception("无法从响应中提取JSON内容")
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

class AppIdLLMClient(LLMClient):
    """基于AppId列表的LLM客户端"""
    
    def __init__(self, appid_list: List[str], model: str = "gpt-3.5-turbo", base_url: Optional[str] = None):
        self.appid_list = appid_list
        self.model = model
        self.current_appid_index = 0
        self.failed_appids = set()  # 记录失败的AppId
        self.base_url = base_url or settings.openai_base_url
    
    def _get_next_appid(self) -> str:
        """获取下一个可用的AppId（轮询方式）"""
        if not self.appid_list:
            raise Exception("没有可用的AppId")
        
        # 过滤掉失败的AppId
        available_appids = [appid for appid in self.appid_list if appid not in self.failed_appids]
        if not available_appids:
            # 如果所有AppId都失败了，重置失败列表
            self.failed_appids.clear()
            available_appids = self.appid_list
        
        appid = available_appids[self.current_appid_index % len(available_appids)]
        self.current_appid_index = (self.current_appid_index + 1) % len(available_appids)
        return appid
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        max_retries = settings.llm_max_retries
        base_wait = max(0.5, settings.llm_retry_wait_seconds)
        for attempt in range(max_retries):
            try:
                appid = self._get_next_appid()
                print(f"🔑 使用AppId: {appid} (尝试 {attempt + 1}/{max_retries})")
                
                # 尝试调用实际的API
                response = await self._call_appid_api(prompt, appid, **kwargs)
                if response:
                    return response
                
                # 如果API调用失败，标记这个AppId为失败
                self.failed_appids.add(appid)
                print(f"⚠️ AppId {appid} 调用失败，尝试下一个")
                
            except Exception as e:
                print(f"❌ AppId API调用异常: {str(e)}")
                if attempt < max_retries - 1:
                    # 指数退避等待
                    wait_seconds = min(base_wait * (2 ** attempt), 60.0)
                    await asyncio.sleep(wait_seconds)
                else:
                    # 所有重试都失败了，返回降级响应
                    return await self._fallback_response(prompt)
        
        return await self._fallback_response(prompt)
    
    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """生成结构化响应"""
        try:
            # 先尝试生成普通响应
            response = await self.generate_response(prompt)
            
            # 尝试解析为JSON
            import json
            try:
                if response and response.strip():
                    return json.loads(response)
            except json.JSONDecodeError:
                pass
            
            # 如果解析失败，返回符合schema的降级数据
            return self._generate_fallback_structured_response(schema)
                
        except Exception as e:
            print(f"❌ AppId结构化响应生成失败: {str(e)}")
            return self._generate_fallback_structured_response(schema)
    
    async def _call_appid_api(self, prompt: str, appid: str, **kwargs) -> Optional[str]:
        """调用AppId API (通过 OpenAI 兼容接口，使用 appid 作为 api_key)"""
        try:
            # 为该 appid 构建临时客户端
            client = openai.AsyncOpenAI(api_key=appid, base_url=self.base_url)
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            top_p = kwargs.get("top_p", 1.0)
            frequency_penalty = kwargs.get("frequency_penalty", 0.0)
            presence_penalty = kwargs.get("presence_penalty", 0.0)

            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty
                )
                return response.choices[0].message.content
            except Exception as e:
                # 限流处理：遇到429或RateLimit相关报错时，返回None让上层重试
                err_text = str(e).lower()
                if "rate" in err_text or "429" in err_text or "limit" in err_text:
                    return None
                raise
        except Exception as e:
            print(f"❌ AppId {appid} API调用异常: {str(e)}")
            return None
    
    async def _fallback_response(self, prompt: str) -> str:
        """降级响应"""
        print("🔄 使用降级响应策略")
        return f"降级响应: 无法获取LLM服务，使用基础处理 - {prompt[:100]}..."
    
    def _generate_fallback_structured_response(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """生成降级的结构化响应"""
        if "complexity" in schema:
            return {"complexity": "unknown", "reason": "无法获取LLM服务"}
        elif "tasks" in schema:
            return {
                "tasks": [
                    {"id": "fallback_task", "type": "search", "description": "降级任务处理"}
                ],
                "dependencies": {}
            }
        else:
            return {"result": "降级响应", "error": "LLM服务不可用"}

class LLMClientFactory:
    """LLM客户端工厂"""
    
    @staticmethod
    def create_client(provider: str = "openai", **kwargs) -> LLMClient:
        """创建LLM客户端"""
        if provider == "openai":
            api_key = kwargs.get("api_key") or settings.openai_api_key
            if not api_key:
                raise Exception("OpenAI API密钥未配置")
            return OpenAIClient(
                api_key=api_key,
                model=kwargs.get("model", "gpt-3.5-turbo"),
                base_url=kwargs.get("base_url") or settings.openai_base_url,
            )
        elif provider == "mock":
            return MockLLMClient()
        elif provider == "appid":
            # 使用appid_list配置的客户端
            appid_list = kwargs.get("appid_list") or settings.appid_list
            if not appid_list:
                raise Exception("appid_list未配置")
            return AppIdLLMClient(
                appid_list=appid_list,
                model=kwargs.get("model", "gpt-3.5-turbo"),
                base_url=kwargs.get("base_url") or settings.openai_base_url,
            )
        else:
            raise Exception(f"不支持的LLM提供商: {provider}")

# 全局LLM客户端实例
llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    """获取全局LLM客户端"""
    global llm_client
    if llm_client is None:
        # 根据配置选择客户端类型
        if settings.openai_api_key:
            provider = "openai"
        elif settings.appid_list:
            provider = "appid"
        else:
            provider = "mock"
        
        llm_client = LLMClientFactory.create_client(provider=provider)
    return llm_client

def set_llm_client(client: LLMClient):
    """设置全局LLM客户端"""
    global llm_client
    llm_client = client
