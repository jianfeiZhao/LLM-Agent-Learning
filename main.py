"""
旅游攻略小助手 - 主程序入口
基于Swarm框架的多Agent系统
"""
import asyncio
import sys
from typing import Optional

from swarm_coordinator import SwarmCoordinator
from models import AgentResponse
from llm_client import get_llm_client, set_llm_client, LLMClientFactory
from config import settings

class TravelAssistantApp:
    """旅游攻略小助手应用"""
    
    def __init__(self):
        self.swarm = None
        self.is_running = False
    
    async def start(self):
        """启动应用"""
        print("🌟 欢迎使用旅游攻略小助手！")
        print("基于Swarm框架的多Agent智能系统")
        print("=" * 50)
        
        # 初始化LLM客户端
        try:
            # 根据配置选择客户端类型
            if settings.openai_api_key:
                provider = "openai"
                kwargs = {"api_key": settings.openai_api_key, "model": settings.llm_model, "base_url": settings.openai_base_url}
            elif settings.appid_list:
                provider = "appid"
                kwargs = {"appid_list": settings.appid_list, "model": settings.llm_model, "base_url": settings.openai_base_url}
            else:
                provider = "mock"
                kwargs = {}
            
            llm_client = LLMClientFactory.create_client(provider=provider, **kwargs)
            set_llm_client(llm_client)
            print(f"✅ LLM客户端已初始化: {provider}")
            if provider == "appid":
                print(f"📋 配置了 {len(settings.appid_list)} 个AppId")
        except Exception as e:
            print(f"⚠️ LLM客户端初始化失败: {str(e)}")
            print("将使用模拟客户端")
            # 失败时回退为mock客户端
            llm_client = LLMClientFactory.create_client(provider="mock")
            set_llm_client(llm_client)
        
        # 启动Swarm协调器（在设置全局LLM客户端之后再创建）
        self.swarm = SwarmCoordinator(max_concurrent_tasks=5)
        await self.swarm.start()
        self.is_running = True
        
        print("✅ 系统已启动，可以开始提问了！")
        print("输入 'quit' 或 'exit' 退出程序")
        print("输入 'status' 查看系统状态")
        print("输入 'help' 查看帮助信息")
        print("输入 'prompt' 进入Prompt管理")
        print("-" * 50)
    
    async def stop(self):
        """停止应用"""
        print("\n🛑 正在关闭系统...")
        await self.swarm.stop()
        self.is_running = False
        print("✅ 系统已关闭，再见！")
    
    async def run_interactive(self):
        """运行交互式模式"""
        await self.start()
        
        try:
            while self.is_running:
                try:
                    # 获取用户输入
                    user_input = await self._get_user_input()
                    
                    if not user_input:
                        continue
                    
                    # 处理特殊命令
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    elif user_input.lower() == 'status':
                        await self._show_status()
                        continue
                    elif user_input.lower() == 'help':
                        self._show_help()
                        continue
                    elif user_input.lower() == 'prompt':
                        self._open_prompt_manager()
                        continue
                    
                    # 处理查询
                    await self._process_user_query(user_input)
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️ 检测到中断信号...")
                    break
                except Exception as e:
                    print(f"❌ 处理输入时出错: {str(e)}")
        
        finally:
            await self.stop()
    
    async def run_demo(self):
        """运行演示模式"""
        await self.start()
        
        # 演示查询列表
        demo_queries = [
            "汉武大帝的名字是什么？",
            "汉武大帝和凯撒大帝谁更年长？",
            "北京有什么好玩的景点？",
            "上海的美食推荐",
            "帮我规划一个北京3日游"
        ]
        
        print("🎭 开始演示模式...")
        print("=" * 50)
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n📝 演示查询 {i}: {query}")
            print("-" * 30)
            
            await self._process_user_query(query)
            
            # 等待用户确认继续
            if i < len(demo_queries):
                input("\n按回车键继续下一个演示...")
        
        print("\n🎉 演示完成！")
        await self.stop()
    
    async def _get_user_input(self) -> str:
        """获取用户输入"""
        try:
            return input("\n💬 请输入您的问题: ").strip()
        except EOFError:
            return ""
    
    async def _process_user_query(self, query: str):
        """处理用户查询"""
        try:
            print(f"🔄 正在处理: {query}")
            
            # 提交查询到Swarm
            query_id = await self.swarm.process_query(query)
            
            # 等待结果
            print("⏳ 正在分析...")
            result = await self._wait_for_result(query_id)
            
            if result:
                if result.success:
                    print("\n✅ 回答:")
                    print("=" * 50)
                    print(result.result)
                    print("=" * 50)
                else:
                    print(f"\n❌ 处理失败: {result.error}")
            else:
                print("❌ 查询超时或失败")
                
        except Exception as e:
            print(f"❌ 处理查询时出错: {str(e)}")
    
    async def _wait_for_result(self, query_id: str, timeout: float = 30.0) -> Optional[AgentResponse]:
        """等待查询结果"""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            result = await self.swarm.get_query_result(query_id)
            if result is not None:
                return result
            
            await asyncio.sleep(0.5)
        
        return None
    
    async def _show_status(self):
        """显示系统状态"""
        status = await self.swarm.get_status()
        
        print("\n📊 系统状态:")
        print("=" * 30)
        print(f"状态: {status['status']}")
        print(f"总查询数: {status['metrics']['total_queries']}")
        print(f"成功查询: {status['metrics']['successful_queries']}")
        print(f"失败查询: {status['metrics']['failed_queries']}")
        print(f"活跃任务: {status['metrics']['active_tasks']}")
        print(f"成功率: {status['metrics']['success_rate']:.2%}")
        print(f"运行时间: {status['metrics']['uptime_seconds']:.1f}秒")
        print("=" * 30)
    
    def _show_help(self):
        """显示帮助信息"""
        print("\n📖 帮助信息:")
        print("=" * 30)
        print("这是一个基于Swarm框架的多Agent旅游攻略小助手")
        print("\n支持的查询类型:")
        print("• 历史人物信息查询")
        print("• 历史人物比较分析")
        print("• 城市旅游攻略")
        print("• 旅游行程规划")
        print("\n示例查询:")
        print("• 汉武大帝是谁？")
        print("• 汉武大帝和凯撒大帝谁更年长？")
        print("• 北京有什么好玩的？")
        print("• 帮我规划上海3日游")
        print("\n特殊命令:")
        print("• status - 查看系统状态")
        print("• help - 显示帮助信息")
        print("• prompt - 进入Prompt管理")
        print("• quit/exit - 退出程序")
        print("=" * 30)
    
    def _open_prompt_manager(self):
        """打开Prompt管理工具"""
        print("\n🔧 进入Prompt管理工具...")
        print("提示: 输入 'quit' 返回主程序")
        
        try:
            from prompt_manager import PromptManagerCLI
            cli = PromptManagerCLI()
            cli.list_agents()
            
            while True:
                command = input("\nPrompt管理> ").strip().split()
                
                if not command or command[0] == "quit":
                    break
                elif command[0] == "list":
                    cli.list_agents()
                elif command[0] == "show" and len(command) > 1:
                    cli.show_agent_prompt(command[1])
                elif command[0] == "update" and len(command) > 1:
                    agent_name = command[1]
                    print(f"更新 {agent_name} Agent的Prompt (直接回车保持原值):")
                    
                    system_prompt = input("系统Prompt: ").strip() or None
                    user_prompt = input("用户Prompt模板: ").strip() or None
                    
                    temp_input = input("温度 (0.0-1.0): ").strip()
                    temperature = float(temp_input) if temp_input else None
                    
                    tokens_input = input("最大Token数: ").strip()
                    max_tokens = int(tokens_input) if tokens_input else None
                    
                    cli.update_agent_prompt(agent_name, system_prompt, user_prompt, temperature, max_tokens)
                elif command[0] == "reset":
                    cli.reset_to_default()
                elif command[0] == "backup":
                    backup_file = command[1] if len(command) > 1 else "prompt_backup.json"
                    cli.backup_prompts(backup_file)
                elif command[0] == "restore":
                    backup_file = command[1] if len(command) > 1 else "prompt_backup.json"
                    cli.restore_prompts(backup_file)
                else:
                    print("❌ 无效命令")
                    print("可用命令: list, show <agent>, update <agent>, reset, backup, restore, quit")
            
            print("✅ 已退出Prompt管理工具")
            
        except Exception as e:
            print(f"❌ 打开Prompt管理工具失败: {str(e)}")

async def main():
    """主函数"""
    app = TravelAssistantApp()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            await app.run_demo()
        elif sys.argv[1] == "interactive":
            await app.run_interactive()
        else:
            print("用法: python main.py [demo|interactive]")
            print("  demo - 运行演示模式")
            print("  interactive - 运行交互模式（默认）")
    else:
        # 默认运行交互模式
        await app.run_interactive()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，再见！")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {str(e)}")
        sys.exit(1)
