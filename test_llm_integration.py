"""
LLM集成测试脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_client import get_llm_client, LLMClientFactory
from prompt_templates import get_prompt_manager, AgentType
from config import settings

async def test_llm_client():
    """测试LLM客户端"""
    print("🧪 测试LLM客户端...")
    
    try:
        # 创建LLM客户端
        llm_client = get_llm_client()
        print(f"✅ LLM客户端创建成功: {type(llm_client).__name__}")
        
        # 测试简单生成
        response = await llm_client.generate_response("你好，请简单介绍一下自己")
        print(f"📝 简单生成测试: {response[:100]}...")
        
        # 测试结构化生成
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        structured_response = await llm_client.generate_structured_response(
            "请生成一个人的基本信息", schema
        )
        print(f"📊 结构化生成测试: {structured_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM客户端测试失败: {str(e)}")
        return False

async def test_prompt_manager():
    """测试Prompt管理器"""
    print("\n🧪 测试Prompt管理器...")
    
    try:
        prompt_manager = get_prompt_manager()
        
        # 测试获取模板
        for agent_type in AgentType:
            template = prompt_manager.get_template(agent_type)
            if template:
                print(f"✅ {agent_type.value} Agent模板: {template.system_prompt[:50]}...")
            else:
                print(f"❌ {agent_type.value} Agent模板未找到")
        
        # 测试格式化Prompt
        system_prompt, user_prompt = prompt_manager.format_prompt(
            AgentType.MASTER, query="测试查询"
        )
        print(f"📝 Master Agent Prompt格式化测试:")
        print(f"   系统Prompt: {system_prompt[:50]}...")
        print(f"   用户Prompt: {user_prompt}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt管理器测试失败: {str(e)}")
        return False

async def test_agent_integration():
    """测试Agent集成"""
    print("\n🧪 测试Agent集成...")
    
    try:
        from agents.master_agent import MasterAgent
        
        # 创建Master Agent
        master_agent = MasterAgent()
        print("✅ Master Agent创建成功")
        
        # 测试简单查询
        print("📝 测试简单查询...")
        result = await master_agent.process_query("汉武大帝是谁？")
        
        if result.success:
            print(f"✅ 简单查询测试成功: {result.result[:100]}...")
        else:
            print(f"❌ 简单查询测试失败: {result.error}")
        
        # 测试复杂查询
        print("📝 测试复杂查询...")
        result = await master_agent.process_query("汉武大帝和凯撒大帝谁更年长？")
        
        if result.success:
            print(f"✅ 复杂查询测试成功: {result.result[:100]}...")
        else:
            print(f"❌ 复杂查询测试失败: {result.error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent集成测试失败: {str(e)}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始LLM集成测试...")
    print("=" * 50)
    
    tests = [
        test_llm_client,
        test_prompt_manager,
        test_agent_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！LLM集成成功！")
    else:
        print("⚠️ 部分测试失败，请检查配置")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
