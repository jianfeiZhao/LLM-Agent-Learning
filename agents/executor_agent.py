"""
Executor Agent - 执行器
负责执行子任务，调用外部工具获取信息，并评估结果是否满足要求
基于大语言模型进行智能任务执行
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from models import DAG, Task, TaskStatus, AgentResponse, TaskType
from tools.search_tool import SearchTool
from tools.calculator_tool import CalculatorTool
from tools.comparison_tool import ComparisonTool
from llm_client import get_llm_client
from prompt_templates import get_prompt_manager, AgentType

class ExecutorAgent:
    """执行器智能体"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.prompt_manager = get_prompt_manager()
        self.search_tool = SearchTool()
        self.calculator_tool = CalculatorTool()
        self.comparison_tool = ComparisonTool()
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def execute_dag(self, dag: DAG) -> Dict[str, AgentResponse]:
        """
        执行DAG中的所有任务
        
        Args:
            dag: 有向无环图
            
        Returns:
            Dict[str, AgentResponse]: 任务执行结果字典
        """
        print(f"⚡ 开始执行DAG，共{len(dag.nodes)}个任务")
        
        results = {}
        completed_tasks = set()
        
        # 按拓扑顺序执行任务
        execution_order = await self._get_execution_order(dag)
        print(f"📋 执行顺序: {execution_order}")
        
        for task_id in execution_order:
            if task_id not in dag.nodes:
                continue
                
            task = dag.nodes[task_id].task
            
            # 检查依赖是否完成
            if not await self._check_dependencies(task_id, dag, completed_tasks):
                print(f"⏳ 任务 {task_id} 的依赖未完成，跳过")
                continue
            
            print(f"🚀 执行任务: {task.description}")
            
            # 执行任务
            result = await self._execute_task(task)
            results[task_id] = result
            
            if result.success:
                completed_tasks.add(task_id)
                print(f"✅ 任务 {task_id} 执行成功")
            else:
                print(f"❌ 任务 {task_id} 执行失败: {result.error}")
        
        return results
    
    async def _get_execution_order(self, dag: DAG) -> List[str]:
        """
        获取任务的拓扑执行顺序
        
        Args:
            dag: 有向无环图
            
        Returns:
            List[str]: 任务ID的执行顺序
        """
        # 使用Kahn算法进行拓扑排序
        in_degree = {}
        for node_id in dag.nodes:
            in_degree[node_id] = len(dag.nodes[node_id].parents)
        
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for child_id in dag.nodes[current].children:
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)
        
        return result
    
    async def _check_dependencies(self, task_id: str, dag: DAG, completed_tasks: set) -> bool:
        """
        检查任务依赖是否完成
        
        Args:
            task_id: 任务ID
            dag: 有向无环图
            completed_tasks: 已完成的任务集合
            
        Returns:
            bool: 依赖是否完成
        """
        if task_id not in dag.nodes:
            return False
        
        dependencies = dag.nodes[task_id].parents
        return all(dep_id in completed_tasks for dep_id in dependencies)
    
    async def _execute_task(self, task: Task) -> AgentResponse:
        """
        使用LLM执行单个任务
        
        Args:
            task: 任务对象
            
        Returns:
            AgentResponse: 执行结果
        """
        task.status = TaskStatus.IN_PROGRESS
        
        for attempt in range(self.max_retries):
            try:
                # 使用LLM执行任务
                result = await self._llm_execute_task(task)
                
                if result.success:
                    task.status = TaskStatus.COMPLETED
                    task.result = result.result
                    task.completed_at = datetime.now().isoformat()
                    return result
                else:
                    print(f"⚠️ 任务执行失败 (尝试 {attempt + 1}/{self.max_retries}): {result.error}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                    
            except Exception as e:
                error_msg = f"执行任务时发生异常: {str(e)}"
                print(f"❌ {error_msg}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    task.status = TaskStatus.FAILED
                    task.error = error_msg
                    return AgentResponse(success=False, error=error_msg)
        
        # 所有重试都失败了
        task.status = TaskStatus.FAILED
        task.error = "任务执行失败，已达到最大重试次数"
        return AgentResponse(success=False, error="任务执行失败，已达到最大重试次数")
    
    async def _llm_execute_task(self, task: Task) -> AgentResponse:
        """
        使用LLM执行任务
        
        Args:
            task: 任务对象
            
        Returns:
            AgentResponse: 执行结果
        """
        try:
            # 格式化Prompt
            system_prompt, user_prompt = self.prompt_manager.format_prompt(
                AgentType.EXECUTOR,
                task_description=task.description,
                task_type=task.type.value
            )
            
            # 获取响应Schema
            response_schema = self.prompt_manager.get_response_schema(AgentType.EXECUTOR)
            
            # 构建完整Prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # 调用LLM生成结构化响应
            if response_schema:
                result = await self.llm_client.generate_structured_response(
                    full_prompt, response_schema
                )
            else:
                response = await self.llm_client.generate_response(full_prompt)
                # 简单的JSON解析
                import json
                result = json.loads(response)
            
            # 转换为AgentResponse格式
            return AgentResponse(
                success=result.get("success", True),
                result=result.get("result", ""),
                error=result.get("error"),
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            # 降级到传统工具执行
            print(f"⚠️ LLM任务执行失败，使用传统工具: {str(e)}")
            return await self._fallback_execute_task(task)
    
    async def _fallback_execute_task(self, task: Task) -> AgentResponse:
        """
        降级任务执行（使用传统工具）
        
        Args:
            task: 任务对象
            
        Returns:
            AgentResponse: 执行结果
        """
        if task.type == TaskType.SEARCH:
            return await self._execute_search_task(task)
        elif task.type == TaskType.CALCULATE:
            return await self._execute_calculate_task(task)
        elif task.type == TaskType.COMPARE:
            return await self._execute_compare_task(task)
        else:
            return AgentResponse(
                success=False,
                error=f"不支持的任务类型: {task.type}"
            )
    
    async def _execute_search_task(self, task: Task) -> AgentResponse:
        """
        执行搜索任务
        
        Args:
            task: 任务对象
            
        Returns:
            AgentResponse: 执行结果
        """
        try:
            # 从任务描述中提取搜索关键词
            search_query = self._extract_search_query(task.description)
            
            # 调用搜索工具
            result = await self.search_tool.search(search_query)
            
            if result.success:
                return AgentResponse(
                    success=True,
                    result=result.result,
                    metadata={"tool": "search", "query": search_query}
                )
            else:
                return AgentResponse(
                    success=False,
                    error=f"搜索失败: {result.error}"
                )
                
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"执行搜索任务时出错: {str(e)}"
            )
    
    async def _execute_calculate_task(self, task: Task) -> AgentResponse:
        """
        执行计算任务
        
        Args:
            task: 任务对象
            
        Returns:
            AgentResponse: 执行结果
        """
        try:
            # 从任务描述中提取计算内容
            calculation_query = self._extract_calculation_query(task.description)
            
            # 调用计算工具
            result = await self.calculator_tool.calculate(calculation_query)
            
            if result.success:
                return AgentResponse(
                    success=True,
                    result=result.result,
                    metadata={"tool": "calculator", "query": calculation_query}
                )
            else:
                return AgentResponse(
                    success=False,
                    error=f"计算失败: {result.error}"
                )
                
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"执行计算任务时出错: {str(e)}"
            )
    
    async def _execute_compare_task(self, task: Task) -> AgentResponse:
        """
        执行比较任务
        
        Args:
            task: 任务对象
            
        Returns:
            AgentResponse: 执行结果
        """
        try:
            # 从任务描述中提取比较内容
            comparison_query = self._extract_comparison_query(task.description)
            
            # 调用比较工具
            result = await self.comparison_tool.compare(comparison_query)
            
            if result.success:
                return AgentResponse(
                    success=True,
                    result=result.result,
                    metadata={"tool": "comparison", "query": comparison_query}
                )
            else:
                return AgentResponse(
                    success=False,
                    error=f"比较失败: {result.error}"
                )
                
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"执行比较任务时出错: {str(e)}"
            )
    
    def _extract_search_query(self, description: str) -> str:
        """
        从任务描述中提取搜索查询
        
        Args:
            description: 任务描述
            
        Returns:
            str: 搜索查询
        """
        # 简单的关键词提取逻辑
        # 在实际应用中，这里可以使用更复杂的NLP技术
        
        if "汉武大帝" in description or "汉武帝" in description:
            return "汉武大帝 出生日期 历史"
        elif "凯撒大帝" in description or "凯撒" in description:
            return "凯撒大帝 出生日期 历史"
        elif "北京" in description:
            return "北京 旅游景点 攻略"
        elif "上海" in description:
            return "上海 旅游景点 攻略"
        else:
            return description
    
    def _extract_calculation_query(self, description: str) -> str:
        """
        从任务描述中提取计算查询
        
        Args:
            description: 任务描述
            
        Returns:
            str: 计算查询
        """
        if "年龄" in description:
            return "年龄计算"
        else:
            return description
    
    def _extract_comparison_query(self, description: str) -> str:
        """
        从任务描述中提取比较查询
        
        Args:
            description: 任务描述
            
        Returns:
            str: 比较查询
        """
        if "汉武大帝" in description and "凯撒大帝" in description:
            return "汉武大帝 vs 凯撒大帝 年龄比较"
        else:
            return description
