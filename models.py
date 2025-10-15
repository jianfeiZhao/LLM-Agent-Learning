"""
数据模型定义
"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
from enum import Enum

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(str, Enum):
    """任务类型枚举"""
    SIMPLE_QUERY = "simple_query"
    COMPLEX_QUERY = "complex_query"
    SEARCH = "search"
    CALCULATE = "calculate"
    COMPARE = "compare"
    GENERATE = "generate"

class Task(BaseModel):
    """任务模型"""
    id: str
    type: TaskType
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = []
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class DAGNode(BaseModel):
    """DAG节点模型"""
    task_id: str
    task: Task
    children: List[str] = []
    parents: List[str] = []

class DAG(BaseModel):
    """有向无环图模型"""
    nodes: Dict[str, DAGNode] = {}
    root_nodes: List[str] = []
    leaf_nodes: List[str] = []

class QueryComplexity(str, Enum):
    """查询复杂度枚举"""
    SIMPLE = "simple"
    COMPLEX = "complex"

class UserQuery(BaseModel):
    """用户查询模型"""
    query: str
    complexity: Optional[QueryComplexity] = None
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Agent响应模型"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
