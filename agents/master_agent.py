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
            
            # 调用LLM
            response = await self.llm_client.generate_response(
                full_prompt,
                **generation_params
            )
            
            # 解析响应
            if "complex" in response.lower():
                return QueryComplexity.COMPLEX
            else:
                return QueryComplexity.SIMPLE
                
        except Exception as e:
            print(f"⚠️ LLM复杂度分析失败，使用默认策略: {str(e)}")
            # 降级到简单规则判断
            if len(query.query) > 50 or any(keyword in query.query for keyword in ["比较", "对比", "分析", "规划"]):
                return QueryComplexity.COMPLEX
            else:
                return QueryComplexity.SIMPLE
    
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
