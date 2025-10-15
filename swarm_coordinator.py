"""
Swarm协调器
负责协调多个Agent的工作，实现任务调度和负载均衡
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from models import UserQuery, AgentResponse, Task, TaskStatus
from agents.master_agent import MasterAgent

class SwarmStatus(str, Enum):
    """Swarm状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"

@dataclass
class SwarmMetrics:
    """Swarm性能指标"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    average_response_time: float = 0.0
    active_tasks: int = 0
    uptime: float = 0.0

class SwarmCoordinator:
    """Swarm协调器"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.master_agent = MasterAgent()
        self.status = SwarmStatus.IDLE
        self.metrics = SwarmMetrics()
        self.start_time = datetime.now()
        self.active_queries: Dict[str, asyncio.Task] = {}
        self.task_queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
        
    async def start(self):
        """启动Swarm协调器"""
        print("🚀 启动Swarm协调器...")
        
        # 启动工作线程
        for i in range(self.max_concurrent_tasks):
            worker_task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker_task)
        
        self.status = SwarmStatus.IDLE
        print(f"✅ Swarm协调器已启动，工作线程数: {self.max_concurrent_tasks}")
    
    async def stop(self):
        """停止Swarm协调器"""
        print("🛑 停止Swarm协调器...")
        
        self.status = SwarmStatus.SHUTDOWN
        
        # 取消所有活跃查询
        for query_id, task in self.active_queries.items():
            task.cancel()
        
        # 停止工作线程
        for worker_task in self.worker_tasks:
            worker_task.cancel()
        
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        print("✅ Swarm协调器已停止")
    
    async def process_query(self, query: str, query_id: Optional[str] = None) -> str:
        """
        处理用户查询
        
        Args:
            query: 用户查询
            query_id: 查询ID（可选）
            
        Returns:
            str: 查询ID
        """
        if query_id is None:
            query_id = str(uuid.uuid4())
        
        print(f"📝 接收查询 [{query_id}]: {query}")
        
        # 检查是否超过最大并发数
        if len(self.active_queries) >= self.max_concurrent_tasks:
            raise Exception("系统繁忙，请稍后再试")
        
        # 创建查询任务
        query_task = asyncio.create_task(self._process_query_async(query, query_id))
        self.active_queries[query_id] = query_task
        
        # 更新指标
        self.metrics.total_queries += 1
        self.metrics.active_tasks = len(self.active_queries)
        
        return query_id
    
    async def get_query_result(self, query_id: str) -> Optional[AgentResponse]:
        """
        获取查询结果
        
        Args:
            query_id: 查询ID
            
        Returns:
            Optional[AgentResponse]: 查询结果
        """
        if query_id not in self.active_queries:
            return None
        
        query_task = self.active_queries[query_id]
        
        if query_task.done():
            try:
                result = await query_task
                # 从活跃查询中移除
                del self.active_queries[query_id]
                self.metrics.active_tasks = len(self.active_queries)
                return result
            except Exception as e:
                print(f"❌ 查询 {query_id} 执行失败: {str(e)}")
                del self.active_queries[query_id]
                self.metrics.active_tasks = len(self.active_queries)
                return AgentResponse(success=False, error=str(e))
        else:
            return None  # 查询仍在进行中
    
    async def get_status(self) -> Dict[str, Any]:
        """
        获取Swarm状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        current_time = datetime.now()
        uptime = (current_time - self.start_time).total_seconds()
        
        self.metrics.uptime = uptime
        self.metrics.active_tasks = len(self.active_queries)
        
        return {
            "status": self.status.value,
            "metrics": {
                "total_queries": self.metrics.total_queries,
                "successful_queries": self.metrics.successful_queries,
                "failed_queries": self.metrics.failed_queries,
                "active_tasks": self.metrics.active_tasks,
                "uptime_seconds": self.metrics.uptime,
                "success_rate": (
                    self.metrics.successful_queries / self.metrics.total_queries 
                    if self.metrics.total_queries > 0 else 0
                )
            },
            "active_queries": list(self.active_queries.keys())
        }
    
    async def _worker(self, worker_name: str):
        """工作线程"""
        print(f"👷 工作线程 {worker_name} 已启动")
        
        while self.status != SwarmStatus.SHUTDOWN:
            try:
                # 从队列中获取任务
                task_data = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=1.0
                )
                
                # 处理任务
                await self._handle_task(task_data)
                
            except asyncio.TimeoutError:
                # 超时，继续循环
                continue
            except Exception as e:
                print(f"❌ 工作线程 {worker_name} 异常: {str(e)}")
                await asyncio.sleep(1.0)
        
        print(f"👷 工作线程 {worker_name} 已停止")
    
    async def _process_query_async(self, query: str, query_id: str) -> AgentResponse:
        """
        异步处理查询
        
        Args:
            query: 用户查询
            query_id: 查询ID
            
        Returns:
            AgentResponse: 处理结果
        """
        try:
            start_time = datetime.now()
            
            # 调用Master Agent处理查询
            result = await self.master_agent.process_query(query)
            
            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 更新指标
            if result.success:
                self.metrics.successful_queries += 1
            else:
                self.metrics.failed_queries += 1
            
            # 更新平均响应时间
            total_queries = self.metrics.successful_queries + self.metrics.failed_queries
            if total_queries > 0:
                self.metrics.average_response_time = (
                    (self.metrics.average_response_time * (total_queries - 1) + response_time) 
                    / total_queries
                )
            
            print(f"✅ 查询 {query_id} 处理完成，耗时: {response_time:.2f}秒")
            
            return result
            
        except Exception as e:
            print(f"❌ 查询 {query_id} 处理失败: {str(e)}")
            self.metrics.failed_queries += 1
            return AgentResponse(success=False, error=str(e))
    
    async def _handle_task(self, task_data: Dict[str, Any]):
        """处理任务"""
        # 这里可以添加任务处理逻辑
        pass
    
    def get_metrics(self) -> SwarmMetrics:
        """获取性能指标"""
        return self.metrics
