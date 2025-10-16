"""
Planner Agent - 规划器
专为复杂查询设计，将问题拆解为多个子任务，并组织成DAG（有向无环图）
基于大语言模型进行智能任务分解
"""
import uuid
import re
from typing import List, Dict, Set, Tuple, Any
from datetime import datetime

from models import UserQuery, Task, TaskType, TaskStatus, DAG, DAGNode
from llm_client import get_llm_client
from prompt_templates import get_prompt_manager, AgentType

class PlannerAgent:
    """规划器智能体"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.prompt_manager = get_prompt_manager()
    
    async def plan_tasks(self, query: UserQuery) -> DAG:
        """
        使用LLM将复杂查询分解为子任务并构建DAG
        
        Args:
            query: 用户查询对象
            
        Returns:
            DAG: 任务有向无环图
        """
        print(f"📋 开始规划任务: {query.query}")
        
        try:
            # 使用LLM进行任务规划
            planning_result = await self._llm_plan_tasks(query.query)
            
            # 从LLM结果生成任务
            tasks = self._create_tasks_from_planning(planning_result)
            print(f"📝 生成{len(tasks)}个子任务")
            
            # 构建DAG
            dag = await self._build_dag_from_planning(tasks, planning_result)
            print(f"🌐 DAG构建完成，根节点: {len(dag.root_nodes)}, 叶节点: {len(dag.leaf_nodes)}")
            
            return dag
            
        except Exception as e:
            print(f"⚠️ LLM任务规划失败，使用默认策略: {str(e)}")
            # 降级到基于规则的任务规划
            return await self._fallback_plan_tasks(query)
    
    async def _llm_plan_tasks(self, query: str) -> Dict[str, Any]:
        """
        使用LLM进行任务规划
        
        Args:
            query: 用户查询
            
        Returns:
            Dict[str, Any]: 规划结果
        """
        try:
            # 格式化Prompt
            system_prompt, user_prompt = self.prompt_manager.format_prompt(
                AgentType.PLANNER,
                query=query
            )
            
            # 获取响应Schema
            response_schema = self.prompt_manager.get_response_schema(AgentType.PLANNER)
            
            # 构建完整Prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # 调用LLM生成结构化响应
            if response_schema:
                result = await self.llm_client.generate_structured_response(
                    full_prompt, response_schema
                )
                # 确保结构化响应包含必要字段
                if not isinstance(result, dict):
                    result = {"tasks": [], "dependencies": {}}
                if "tasks" not in result:
                    result["tasks"] = []
                if "dependencies" not in result:
                    result["dependencies"] = {}
            else:
                response = await self.llm_client.generate_response(full_prompt)
                # 尝试解析JSON，如果失败则创建默认结构
                import json
                try:
                    # 检查响应是否为空或只包含空白字符
                    if not response or not response.strip():
                        raise json.JSONDecodeError("Empty response", response, 0)
                    result = json.loads(response)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON解析失败: {str(e)}")
                    print(f"📝 原始响应: {response[:200]}...")
                    # 如果解析失败，创建默认规划结构
                    result = {
                        "tasks": [
                            {
                                "id": "task1",
                                "type": "search",
                                "description": f"搜索相关信息: {query}"
                            }
                        ],
                        "dependencies": {}
                    }
            
            return result
            
        except Exception as e:
            raise Exception(f"LLM任务规划失败: {str(e)}")
    
    def _create_tasks_from_planning(self, planning_result: Dict[str, Any]) -> List[Task]:
        """
        从规划结果创建任务列表
        
        Args:
            planning_result: LLM规划结果
            
        Returns:
            List[Task]: 任务列表
        """
        tasks = []
        task_data = planning_result.get("tasks", [])
        
        for task_info in task_data:
            task = Task(
                id=str(uuid.uuid4()),
                type=TaskType(task_info.get("type", "search")),
                description=task_info.get("description", ""),
                status=TaskStatus.PENDING,
                created_at=datetime.now().isoformat()
            )
            tasks.append(task)
        
        return tasks
    
    async def _build_dag_from_planning(self, tasks: List[Task], planning_result: Dict[str, Any]) -> DAG:
        """
        从规划结果构建DAG
        
        Args:
            tasks: 任务列表
            planning_result: 规划结果
            
        Returns:
            DAG: 有向无环图
        """
        dag = DAG()
        dependencies = planning_result.get("dependencies", {})
        
        # 创建节点
        for task in tasks:
            dag_node = DAGNode(
                task_id=task.id,
                task=task,
                children=[],
                parents=dependencies.get(task.id, [])
            )
            dag.nodes[task.id] = dag_node
        
        # 建立子节点关系
        for task_id, deps in dependencies.items():
            for dep_id in deps:
                if dep_id in dag.nodes:
                    dag.nodes[dep_id].children.append(task_id)
        
        # 找到根节点和叶节点
        dag.root_nodes = [
            task_id for task_id, node in dag.nodes.items() 
            if not node.parents
        ]
        
        dag.leaf_nodes = [
            task_id for task_id, node in dag.nodes.items() 
            if not node.children
        ]
        
        return dag
    
    async def _fallback_plan_tasks(self, query: UserQuery) -> DAG:
        """
        降级任务规划（基于规则）
        
        Args:
            query: 用户查询对象
            
        Returns:
            DAG: 任务有向无环图
        """
        print("🔄 使用降级任务规划策略")
        
        # 1. 分析查询内容，识别需要的信息
        required_info = await self._analyze_required_information(query.query)
        print(f"🔍 识别到需要的信息: {required_info}")
        
        # 2. 生成子任务
        tasks = await self._generate_subtasks(query.query, required_info)
        print(f"📝 生成{len(tasks)}个子任务")
        
        # 3. 分析任务依赖关系
        dependencies = await self._analyze_dependencies(tasks)
        print(f"🔗 分析任务依赖关系完成")
        
        # 4. 构建DAG
        dag = await self._build_dag(tasks, dependencies)
        print(f"🌐 DAG构建完成，根节点: {len(dag.root_nodes)}, 叶节点: {len(dag.leaf_nodes)}")
        
        return dag
    
    async def _analyze_required_information(self, query: str) -> List[str]:
        """
        分析查询需要的信息
        
        Args:
            query: 查询字符串
            
        Returns:
            List[str]: 需要的信息列表
        """
        required_info = []
        
        # 识别人物信息
        if re.search(r"(汉武大帝|汉武帝|刘彻)", query):
            required_info.append("汉武大帝的出生日期")
        
        if re.search(r"(凯撒大帝|凯撒|恺撒)", query):
            required_info.append("凯撒大帝的出生日期")
        
        # 识别地点信息
        if re.search(r"(北京|上海|广州|深圳|杭州|成都|西安|南京|武汉|重庆)", query):
            city = re.search(r"(北京|上海|广州|深圳|杭州|成都|西安|南京|武汉|重庆)", query).group(1)
            required_info.append(f"{city}的旅游景点信息")
            required_info.append(f"{city}的交通信息")
            required_info.append(f"{city}的住宿信息")
        
        # 识别时间信息
        if re.search(r"(年龄|年长|年轻|出生|生日)", query):
            required_info.append("年龄计算")
        
        # 识别比较信息
        if re.search(r"(比较|对比|谁更|哪个|哪个更)", query):
            required_info.append("比较分析")
        
        return required_info
    
    async def _generate_subtasks(self, query: str, required_info: List[str]) -> List[Task]:
        """
        根据所需信息生成子任务
        
        Args:
            query: 查询字符串
            required_info: 需要的信息列表
            
        Returns:
            List[Task]: 子任务列表
        """
        tasks = []
        
        for i, info in enumerate(required_info):
            task_type = self._determine_task_type(info)
            
            task = Task(
                id=str(uuid.uuid4()),
                type=task_type,
                description=f"获取信息: {info}",
                status=TaskStatus.PENDING,
                created_at=datetime.now().isoformat()
            )
            
            tasks.append(task)
        
        return tasks
    
    def _determine_task_type(self, info: str) -> TaskType:
        """
        根据信息内容确定任务类型
        
        Args:
            info: 信息描述
            
        Returns:
            TaskType: 任务类型
        """
        if "搜索" in info or "查询" in info or "获取" in info:
            return TaskType.SEARCH
        elif "计算" in info or "年龄" in info:
            return TaskType.CALCULATE
        elif "比较" in info or "对比" in info:
            return TaskType.COMPARE
        else:
            return TaskType.SEARCH
    
    async def _analyze_dependencies(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """
        分析任务依赖关系
        
        Args:
            tasks: 任务列表
            
        Returns:
            Dict[str, List[str]]: 依赖关系字典，key为任务ID，value为依赖的任务ID列表
        """
        dependencies = {}
        
        # 简单的依赖分析逻辑
        # 在实际应用中，这里可以使用更复杂的NLP技术来分析依赖关系
        
        for task in tasks:
            deps = []
            
            # 计算任务通常依赖于搜索任务
            if task.type == TaskType.CALCULATE:
                for other_task in tasks:
                    if other_task.type == TaskType.SEARCH and other_task.id != task.id:
                        deps.append(other_task.id)
            
            # 比较任务通常依赖于搜索和计算任务
            elif task.type == TaskType.COMPARE:
                for other_task in tasks:
                    if other_task.type in [TaskType.SEARCH, TaskType.CALCULATE] and other_task.id != task.id:
                        deps.append(other_task.id)
            
            dependencies[task.id] = deps
        
        return dependencies
    
    async def _build_dag(self, tasks: List[Task], dependencies: Dict[str, List[str]]) -> DAG:
        """
        构建有向无环图
        
        Args:
            tasks: 任务列表
            dependencies: 依赖关系字典
            
        Returns:
            DAG: 有向无环图
        """
        dag = DAG()
        
        # 创建节点
        for task in tasks:
            dag_node = DAGNode(
                task_id=task.id,
                task=task,
                children=[],
                parents=dependencies.get(task.id, [])
            )
            dag.nodes[task.id] = dag_node
        
        # 建立子节点关系
        for task_id, deps in dependencies.items():
            for dep_id in deps:
                if dep_id in dag.nodes:
                    dag.nodes[dep_id].children.append(task_id)
        
        # 找到根节点（没有父节点的节点）
        dag.root_nodes = [
            task_id for task_id, node in dag.nodes.items() 
            if not node.parents
        ]
        
        # 找到叶节点（没有子节点的节点）
        dag.leaf_nodes = [
            task_id for task_id, node in dag.nodes.items() 
            if not node.children
        ]
        
        return dag
    
    def validate_dag(self, dag: DAG) -> bool:
        """
        验证DAG是否有效（无环）
        
        Args:
            dag: 有向无环图
            
        Returns:
            bool: 是否有效
        """
        # 使用DFS检测环
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for child_id in dag.nodes[node_id].children:
                if child_id not in visited:
                    if has_cycle(child_id):
                        return True
                elif child_id in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in dag.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    return False
        
        return True
