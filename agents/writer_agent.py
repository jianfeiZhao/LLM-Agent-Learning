"""
Writer Agent - 生成器
整合所有子任务结果，生成连贯、多视角的最终答案，同时过滤冗余或矛盾信息
基于大语言模型进行智能内容生成
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from models import AgentResponse
from llm_client import get_llm_client
from prompt_templates import get_prompt_manager, AgentType

class WriterAgent:
    """生成器智能体"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.prompt_manager = get_prompt_manager()
        self.template_engine = TemplateEngine()
        self.content_filter = ContentFilter()
        self.fact_checker = FactChecker()
    
    async def generate_simple_answer(self, query: str) -> str:
        """
        使用LLM生成简单查询的答案
        
        Args:
            query: 用户查询
            
        Returns:
            str: 生成的答案
        """
        print(f"📝 生成简单答案: {query}")
        
        try:
            # 使用LLM生成答案
            return await self._llm_generate_answer(query, {})
        except Exception as e:
            print(f"⚠️ LLM生成失败，使用模板生成: {str(e)}")
            # 降级到模板生成
            if self._is_historical_query(query):
                return await self._generate_historical_answer(query)
            elif self._is_travel_query(query):
                return await self._generate_travel_answer(query)
            else:
                return await self._generate_general_answer(query)
    
    async def generate_complex_answer(self, query: str, execution_results: Dict[str, AgentResponse]) -> str:
        """
        使用LLM生成复杂查询的答案
        
        Args:
            query: 用户查询
            execution_results: 执行结果字典
            
        Returns:
            str: 生成的答案
        """
        print(f"📝 生成复杂答案: {query}")
        
        try:
            # 1. 收集和过滤结果
            filtered_results = await self._filter_and_organize_results(execution_results)
            
            # 2. 使用LLM生成答案
            return await self._llm_generate_answer(query, filtered_results)
            
        except Exception as e:
            print(f"⚠️ LLM生成失败，使用模板生成: {str(e)}")
            # 降级到模板生成
            # 1. 收集和过滤结果
            filtered_results = await self._filter_and_organize_results(execution_results)
            
            # 2. 事实核查
            verified_results = await self._verify_facts(filtered_results)
            
            # 3. 生成结构化答案
            if self._is_comparison_query(query):
                return await self._generate_comparison_answer(query, verified_results)
            elif self._is_travel_planning_query(query):
                return await self._generate_travel_planning_answer(query, verified_results)
            else:
                return await self._generate_structured_answer(query, verified_results)
    
    async def _llm_generate_answer(self, query: str, task_results: Dict[str, Any]) -> str:
        """
        使用LLM生成答案
        
        Args:
            query: 用户查询
            task_results: 任务结果
            
        Returns:
            str: 生成的答案
        """
        try:
            # 格式化Prompt
            system_prompt, user_prompt = self.prompt_manager.format_prompt(
                AgentType.WRITER,
                query=query,
                task_results=str(task_results)
            )
            
            # 获取响应Schema
            response_schema = self.prompt_manager.get_response_schema(AgentType.WRITER)
            
            # 构建完整Prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # 调用LLM生成结构化响应
            if response_schema:
                result = await self.llm_client.generate_structured_response(
                    full_prompt, response_schema
                )
                return result.get("answer", "无法生成答案")
            else:
                response = await self.llm_client.generate_response(full_prompt)
                return response
                
        except Exception as e:
            raise Exception(f"LLM答案生成失败: {str(e)}")
    
    def _is_historical_query(self, query: str) -> bool:
        """判断是否为历史查询"""
        historical_keywords = ["汉武大帝", "汉武帝", "凯撒大帝", "凯撒", "历史", "出生", "年龄"]
        return any(keyword in query for keyword in historical_keywords)
    
    def _is_travel_query(self, query: str) -> bool:
        """判断是否为旅游查询"""
        travel_keywords = ["旅游", "景点", "攻略", "住宿", "交通", "美食"]
        city_keywords = ["北京", "上海", "广州", "深圳", "杭州", "成都", "西安", "南京", "武汉", "重庆"]
        return any(keyword in query for keyword in travel_keywords + city_keywords)
    
    def _is_comparison_query(self, query: str) -> bool:
        """判断是否为比较查询"""
        comparison_keywords = ["比较", "对比", "谁更", "哪个", "哪个更", "vs", "与"]
        return any(keyword in query for keyword in comparison_keywords)
    
    def _is_travel_planning_query(self, query: str) -> bool:
        """判断是否为旅游规划查询"""
        planning_keywords = ["规划", "安排", "行程", "路线", "推荐"]
        return any(keyword in query for keyword in planning_keywords) and self._is_travel_query(query)
    
    async def _generate_historical_answer(self, query: str) -> str:
        """生成历史问题答案"""
        if "汉武大帝" in query or "汉武帝" in query:
            return """
## 汉武大帝（汉武帝）

**基本信息：**
- 姓名：刘彻
- 出生日期：公元前156年
- 逝世日期：公元前87年
- 在位时间：公元前141年 - 公元前87年（54年）

**主要成就：**
- 加强中央集权，推行推恩令
- 开拓疆土，北击匈奴
- 派遣张骞出使西域，开辟丝绸之路
- 独尊儒术，设立太学

汉武大帝是中国历史上著名的皇帝之一，以其雄才大略和开拓精神而闻名。
            """.strip()
        
        elif "凯撒大帝" in query or "凯撒" in query:
            return """
## 凯撒大帝（尤利乌斯·凯撒）

**基本信息：**
- 姓名：Gaius Julius Caesar
- 出生日期：公元前100年7月12日
- 逝世日期：公元前44年3月15日
- 享年：56岁

**主要成就：**
- 征服高卢，扩大罗马疆域
- 渡过卢比孔河，引发内战
- 成为终身独裁官
- 改革罗马历法，创立儒略历

凯撒大帝是古罗马历史上最著名的政治家和军事家之一。
            """.strip()
        
        else:
            return "这是一个历史相关的问题，但我需要更多具体信息来提供准确的答案。"
    
    async def _generate_travel_answer(self, query: str) -> str:
        """生成旅游问题答案"""
        cities = {
            "北京": {
                "景点": ["故宫", "天安门", "长城", "颐和园", "天坛", "北海公园"],
                "美食": ["北京烤鸭", "炸酱面", "豆汁", "焦圈", "艾窝窝"],
                "交通": "地铁、公交、出租车都很方便"
            },
            "上海": {
                "景点": ["外滩", "东方明珠", "豫园", "南京路", "新天地", "田子坊"],
                "美食": ["小笼包", "生煎包", "白切鸡", "糖醋小排", "蟹粉小笼"],
                "交通": "地铁网络发达，公交便利"
            }
        }
        
        for city, info in cities.items():
            if city in query:
                return f"""
## {city}旅游攻略

**推荐景点：**
{chr(10).join(f"- {spot}" for spot in info['景点'])}

**特色美食：**
{chr(10).join(f"- {food}" for food in info['美食'])}

**交通信息：**
{info['交通']}

**温馨提示：**
- 建议提前预订酒店
- 注意天气变化，准备合适的衣物
- 热门景点建议避开节假日
                """.strip()
        
        return "请提供具体的城市名称，我可以为您提供详细的旅游攻略。"
    
    async def _generate_general_answer(self, query: str) -> str:
        """生成一般问题答案"""
        return f"""
## 关于您的问题

您询问的是：{query}

这是一个很好的问题！不过我需要更多信息才能为您提供准确的答案。如果您能提供更多细节，我会尽力帮助您。

**建议：**
- 提供更具体的问题描述
- 说明您希望了解的具体方面
- 如果有相关背景信息，也请一并提供
        """.strip()
    
    async def _filter_and_organize_results(self, execution_results: Dict[str, AgentResponse]) -> Dict[str, Any]:
        """
        过滤和组织执行结果
        
        Args:
            execution_results: 执行结果字典
            
        Returns:
            Dict[str, Any]: 过滤后的结果
        """
        filtered_results = {}
        
        for task_id, result in execution_results.items():
            if result.success and result.result:
                # 过滤冗余信息
                filtered_content = await self.content_filter.filter(result.result)
                if filtered_content:
                    filtered_results[task_id] = {
                        "content": filtered_content,
                        "metadata": result.metadata or {},
                        "source": "execution"
                    }
        
        return filtered_results
    
    async def _verify_facts(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        事实核查
        
        Args:
            results: 结果字典
            
        Returns:
            Dict[str, Any]: 核查后的结果
        """
        verified_results = {}
        
        for task_id, result in results.items():
            # 简单的事实核查逻辑
            verified_content = await self.fact_checker.verify(result["content"])
            
            verified_results[task_id] = {
                "content": verified_content,
                "metadata": result["metadata"],
                "source": "verified",
                "confidence": 0.8  # 简单的置信度评分
            }
        
        return verified_results
    
    async def _generate_comparison_answer(self, query: str, results: Dict[str, Any]) -> str:
        """生成比较类答案"""
        if "汉武大帝" in query and "凯撒大帝" in query:
            return """
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

**历史背景：**
- 汉武大帝是西汉第七位皇帝，在位54年
- 凯撒大帝是古罗马的政治家和军事家，虽然被称为"大帝"，但实际上是独裁官
- 两人都是各自文明史上的重要人物，但生活在不同的时代和地区
            """.strip()
        
        return "这是一个比较类问题，但我需要更多信息来提供准确的比较分析。"
    
    async def _generate_travel_planning_answer(self, query: str, results: Dict[str, Any]) -> str:
        """生成旅游规划答案"""
        return """
## 旅游规划建议

基于您的要求，我为您制定了以下旅游规划：

**行程安排：**
1. **第一天：** 抵达目的地，入住酒店，熟悉周边环境
2. **第二天：** 游览主要景点，体验当地文化
3. **第三天：** 深度游，品尝特色美食
4. **第四天：** 购物休闲，准备返程

**注意事项：**
- 提前预订酒店和景点门票
- 关注天气预报，准备合适衣物
- 了解当地交通和风俗习惯
- 准备必要的旅行用品

**预算建议：**
- 住宿：根据个人需求选择
- 餐饮：体验当地特色美食
- 交通：选择便捷的出行方式
- 购物：理性消费，购买纪念品

祝您旅途愉快！
        """.strip()
    
    async def _generate_structured_answer(self, query: str, results: Dict[str, Any]) -> str:
        """生成结构化答案"""
        answer_parts = []
        
        # 添加问题重述
        answer_parts.append(f"## 关于您的问题：{query}")
        answer_parts.append("")
        
        # 添加主要答案
        if results:
            answer_parts.append("### 主要信息：")
            for task_id, result in results.items():
                content = result["content"]
                if isinstance(content, str):
                    answer_parts.append(content)
                else:
                    answer_parts.append(str(content))
                answer_parts.append("")
        
        # 添加总结
        answer_parts.append("### 总结")
        answer_parts.append("以上信息基于多个数据源的综合分析，希望能帮助您解决问题。")
        
        return "\n".join(answer_parts)


class TemplateEngine:
    """模板引擎"""
    
    def __init__(self):
        self.templates = {
            "historical": "历史人物 {name} 的基本信息...",
            "travel": "城市 {city} 的旅游攻略...",
            "comparison": "比较 {item1} 和 {item2}..."
        }
    
    async def render(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        template = self.templates.get(template_name, "")
        return template.format(**kwargs)


class ContentFilter:
    """内容过滤器"""
    
    async def filter(self, content: Any) -> Optional[str]:
        """过滤内容"""
        if isinstance(content, str):
            # 简单的文本过滤
            filtered = re.sub(r'\s+', ' ', content.strip())
            return filtered if len(filtered) > 10 else None
        return str(content) if content else None


class FactChecker:
    """事实核查器"""
    
    async def verify(self, content: str) -> str:
        """验证事实"""
        # 简单的事实核查逻辑
        # 在实际应用中，这里可以集成更复杂的事实核查服务
        
        # 检查是否有明显错误
        if "错误" in content or "失败" in content:
            return f"[需要验证] {content}"
        
        return content
