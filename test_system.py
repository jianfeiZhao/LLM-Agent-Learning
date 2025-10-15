"""
系统测试脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from swarm_coordinator import SwarmCoordinator
from models import AgentResponse

async def test_simple_query():
    """测试简单查询"""
    print("🧪 测试简单查询...")
    
    swarm = SwarmCoordinator()
    await swarm.start()
    
    try:
        # 测试简单查询
        query_id = await swarm.process_query("汉武大帝的名字是什么？")
        print(f"📝 查询ID: {query_id}")
        
        # 等待结果
        result = await wait_for_result(swarm, query_id)
        
        if result and result.success:
            print("✅ 简单查询测试通过")
            print(f"📄 结果: {result.result[:100]}...")
        else:
            print("❌ 简单查询测试失败")
            if result:
                print(f"错误: {result.error}")
    
    finally:
        await swarm.stop()

async def test_complex_query():
    """测试复杂查询"""
    print("\n🧪 测试复杂查询...")
    
    swarm = SwarmCoordinator()
    await swarm.start()
    
    try:
        # 测试复杂查询
        query_id = await swarm.process_query("汉武大帝和凯撒大帝谁更年长？")
        print(f"📝 查询ID: {query_id}")
        
        # 等待结果
        result = await wait_for_result(swarm, query_id)
        
        if result and result.success:
            print("✅ 复杂查询测试通过")
            print(f"📄 结果: {result.result[:100]}...")
        else:
            print("❌ 复杂查询测试失败")
            if result:
                print(f"错误: {result.error}")
    
    finally:
        await swarm.stop()

async def test_travel_query():
    """测试旅游查询"""
    print("\n🧪 测试旅游查询...")
    
    swarm = SwarmCoordinator()
    await swarm.start()
    
    try:
        # 测试旅游查询
        query_id = await swarm.process_query("北京有什么好玩的景点？")
        print(f"📝 查询ID: {query_id}")
        
        # 等待结果
        result = await wait_for_result(swarm, query_id)
        
        if result and result.success:
            print("✅ 旅游查询测试通过")
            print(f"📄 结果: {result.result[:100]}...")
        else:
            print("❌ 旅游查询测试失败")
            if result:
                print(f"错误: {result.error}")
    
    finally:
        await swarm.stop()

async def test_system_status():
    """测试系统状态"""
    print("\n🧪 测试系统状态...")
    
    swarm = SwarmCoordinator()
    await swarm.start()
    
    try:
        # 获取系统状态
        status = await swarm.get_status()
        
        print("📊 系统状态:")
        print(f"  状态: {status['status']}")
        print(f"  总查询数: {status['metrics']['total_queries']}")
        print(f"  活跃任务: {status['metrics']['active_tasks']}")
        print(f"  运行时间: {status['metrics']['uptime_seconds']:.1f}秒")
        
        print("✅ 系统状态测试通过")
    
    finally:
        await swarm.stop()

async def wait_for_result(swarm: SwarmCoordinator, query_id: str, timeout: float = 10.0) -> AgentResponse:
    """等待查询结果"""
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        result = await swarm.get_query_result(query_id)
        if result is not None:
            return result
        
        await asyncio.sleep(0.5)
    
    return None

async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始系统测试...")
    print("=" * 50)
    
    try:
        await test_simple_query()
        await test_complex_query()
        await test_travel_query()
        await test_system_status()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_all_tests())
