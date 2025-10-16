"""
Master Agent - 主控智能体
作为系统的"指挥官"，负责分析用户查询的复杂度，并动态组建处理团队
基于大语言模型进行智能决策
"""
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from models import (
    UserQuery, QueryComplexity, Task, TaskType, TaskStatus, 
    AgentResponse, DAG
)
from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.writer_agent import WriterAgent
from llm_client import get_llm_client
from prompt_templates import get_prompt_manager, AgentType

class MasterAgent:
    """主控智能体"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.prompt_manager = get_prompt_manager()
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.writer = WriterAgent()
        self.active_tasks: Dict[str, Task] = {}
        
    async def process_query(self, user_query: str) -> AgentResponse:
        """
        处理用户查询的主入口
        
        Args:
            user_query: 用户查询字符串
            
        Returns:
            AgentResponse: 处理结果
        """
        try:
            # 创建用户查询对象
            query = UserQuery(query=user_query)
            
            # 分析查询复杂度
            complexity = await self._analyze_complexity(query)
            query.complexity = complexity
            
            print(f"🔍 查询复杂度分析: {complexity}")
            
            # 根据复杂度选择处理策略
            if complexity == QueryComplexity.SIMPLE:
                return await self._handle_simple_query(query)
            else:
                return await self._handle_complex_query(query)
                
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Master Agent处理查询时出错: {str(e)}"
            )
    
    async def _analyze_complexity(self, query: UserQuery) -> QueryComplexity:
        """
        使用LLM分析查询复杂度
        
        Args:
            query: 用户查询对象
            
        Returns:
            QueryComplexity: 复杂度级别
        """
        try:
            # 格式化Prompt
            system_prompt, user_prompt = self.prompt_manager.format_prompt(
                AgentType.MASTER,
                query=query.query
            )
            
            # 构建完整Prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # 获取生成参数
            generation_params = self.prompt_manager.get_generation_params(AgentType.MASTER)
            
            # 获取响应Schema
            response_schema = self.prompt_manager.get_response_schema(AgentType.MASTER)
            
            # 调用LLM生成结构化响应
            if response_schema:
                response = await self.llm_client.generate_structured_response(
                    full_prompt,
                    response_schema,
                    **generation_params
                )
                
                # 打印完整的LLM响应
                print(f"🤖 Master Agent分析结果:")
                print(f"   复杂度: {response.get('complexity', 'unknown')}")
                print(f"   理由: {response.get('reason', '无')}")
                print(f"   策略: {response.get('strategy', '无')}")
                
                # 判断复杂度
                if response.get('complexity', '').lower() == 'complex':
                    return QueryComplexity.COMPLEX
                else:
                    return QueryComplexity.SIMPLE
            else:
                # 回退到非结构化响应
                response = await self.llm_client.generate_response(
                    full_prompt,
                    **generation_params
                )
                
                # 打印完整的LLM响应
                print(f"🤖 Master Agent分析结果:")
                print(f"   {response}")
                
                # 解析响应，提取复杂度判断理由
                complexity_reason = self._extract_complexity_reason(response)
                if complexity_reason:
                    print(f"💭 复杂度判断理由: {complexity_reason}")
                
                # 判断复杂度
                if "complex" in response.lower():
                    return QueryComplexity.COMPLEX
                else:
                    return QueryComplexity.SIMPLE
                
        except Exception as e:
            print(f"⚠️ LLM复杂度分析失败，使用默认策略: {str(e)}")
            # 降级到简单规则判断
            if len(query.query) > 50 or any(keyword in query.query for keyword in ["比较", "对比", "分析", "规划"]):
                print(f"💭 降级判断理由: 查询长度({len(query.query)}字符)或包含复杂关键词")
                return QueryComplexity.COMPLEX
            else:
                print(f"💭 降级判断理由: 查询较短且无复杂关键词")
                return QueryComplexity.SIMPLE
    
    def _extract_complexity_reason(self, response: str) -> str:
        """
        从LLM响应中提取复杂度判断理由
        
        Args:
            response: LLM的完整响应
            
        Returns:
            str: 提取的理由，如果无法提取则返回空字符串
        """
        try:
            # 尝试提取理由部分
            lines = response.split('\n')
            reason_lines = []
            
            # 查找包含"理由"、"原因"、"因为"等关键词的行
            for line in lines:
                line = line.strip()
                if any(keyword in line for keyword in ["理由", "原因", "因为", "reason", "because"]):
                    # 清理行内容，移除关键词前缀
                    cleaned_line = line
                    for keyword in ["理由:", "原因:", "因为:", "reason:", "because:"]:
                        if keyword in cleaned_line:
                            cleaned_line = cleaned_line.split(keyword, 1)[1].strip()
                            break
                    if cleaned_line:
                        reason_lines.append(cleaned_line)
            
            # 如果找到理由行，返回第一个
            if reason_lines:
                return reason_lines[0]
            
            # 如果没有找到明确的关键词，尝试提取第一行非空内容作为理由
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('{', '}', '"', "'")):
                    return line
            
            return ""
            
        except Exception:
            return ""
    
    async def _handle_simple_query(self, query: UserQuery) -> AgentResponse:
        """
        处理简单查询
        
        Args:
            query: 用户查询对象
            
        Returns:
            AgentResponse: 处理结果
        """
        print("📝 处理简单查询，直接调用Writer Agent")
        
        # 创建简单任务
        task = Task(
            id=str(uuid.uuid4()),
            type=TaskType.SIMPLE_QUERY,
            description=query.query,
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime.now().isoformat()
        )
        
        self.active_tasks[task.id] = task
        
        try:
            # 直接调用Writer Agent生成答案
            result = await self.writer.generate_simple_answer(query.query)
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now().isoformat()
            
            return AgentResponse(
                success=True,
                result=result,
                metadata={"task_id": task.id, "type": "simple_query"}
            )
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return AgentResponse(
                success=False,
                error=f"处理简单查询失败: {str(e)}"
            )
    
    async def _handle_complex_query(self, query: UserQuery) -> AgentResponse:
        """
        处理复杂查询
        
        Args:
            query: 用户查询对象
            
        Returns:
            AgentResponse: 处理结果
        """
        print("🔧 处理复杂查询，启动Planner进行任务分解")
        
        try:
            # 1. 使用Planner分解任务
            dag = await self.planner.plan_tasks(query)
            print(f"📋 任务分解完成，共{len(dag.nodes)}个子任务")
            
            # 2. 使用Executor执行所有任务
            execution_results = await self.executor.execute_dag(dag)
            print(f"⚡ 任务执行完成，成功{len([r for r in execution_results.values() if r.success])}个")
            
            # 3. 使用Writer整合结果
            final_result = await self.writer.generate_complex_answer(
                query.query, 
                execution_results
            )
            
            return AgentResponse(
                success=True,
                result=final_result,
                metadata={
                    "task_count": len(dag.nodes),
                    "execution_results": execution_results,
                    "type": "complex_query"
                }
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"处理复杂查询失败: {str(e)}"
            )
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象，如果不存在则返回None
        """
        return self.active_tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Task]:
        """
        获取所有任务
        
        Returns:
            Dict[str, Task]: 所有任务字典
        """
        return self.active_tasks.copy()
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                task.status = TaskStatus.CANCELLED
                return True
        return False
