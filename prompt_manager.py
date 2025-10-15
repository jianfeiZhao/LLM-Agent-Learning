"""
Prompt管理工具
允许用户动态修改Agent的Prompt模板
"""
import json
import os
from typing import Dict, Any, Optional
from prompt_templates import get_prompt_manager, AgentType, PromptTemplate

class PromptManagerCLI:
    """Prompt管理命令行工具"""
    
    def __init__(self):
        self.prompt_manager = get_prompt_manager()
    
    def list_agents(self):
        """列出所有Agent"""
        print("🤖 可用的Agent:")
        print("=" * 40)
        for agent_type in AgentType:
            template = self.prompt_manager.get_template(agent_type)
            if template:
                print(f"• {agent_type.value}: {template.system_prompt[:50]}...")
            else:
                print(f"• {agent_type.value}: 无模板")
        print("=" * 40)
    
    def show_agent_prompt(self, agent_name: str):
        """显示指定Agent的Prompt"""
        try:
            agent_type = AgentType(agent_name)
            template = self.prompt_manager.get_template(agent_type)
            
            if not template:
                print(f"❌ 未找到 {agent_name} Agent的模板")
                return
            
            print(f"🤖 {agent_name} Agent的Prompt模板:")
            print("=" * 50)
            print(f"系统Prompt:\n{template.system_prompt}")
            print("\n" + "-" * 30)
            print(f"用户Prompt模板:\n{template.user_prompt_template}")
            print("\n" + "-" * 30)
            print(f"温度: {template.temperature}")
            print(f"最大Token数: {template.max_tokens}")
            if template.response_schema:
                print(f"响应Schema: {json.dumps(template.response_schema, ensure_ascii=False, indent=2)}")
            print("=" * 50)
            
        except ValueError:
            print(f"❌ 无效的Agent名称: {agent_name}")
            print("可用的Agent:", [agent.value for agent in AgentType])
    
    def update_agent_prompt(self, agent_name: str, system_prompt: str = None, 
                          user_prompt_template: str = None, temperature: float = None,
                          max_tokens: int = None):
        """更新指定Agent的Prompt"""
        try:
            agent_type = AgentType(agent_name)
            current_template = self.prompt_manager.get_template(agent_type)
            
            if not current_template:
                print(f"❌ 未找到 {agent_name} Agent的模板")
                return
            
            # 创建新的模板
            new_template = PromptTemplate(
                system_prompt=system_prompt or current_template.system_prompt,
                user_prompt_template=user_prompt_template or current_template.user_prompt_template,
                response_schema=current_template.response_schema,
                temperature=temperature if temperature is not None else current_template.temperature,
                max_tokens=max_tokens if max_tokens is not None else current_template.max_tokens
            )
            
            # 更新模板
            self.prompt_manager.update_template(agent_type, new_template)
            
            # 保存到文件
            self.prompt_manager.save_to_file()
            
            print(f"✅ 已更新 {agent_name} Agent的Prompt模板")
            
        except ValueError:
            print(f"❌ 无效的Agent名称: {agent_name}")
            print("可用的Agent:", [agent.value for agent in AgentType])
        except Exception as e:
            print(f"❌ 更新失败: {str(e)}")
    
    def reset_to_default(self):
        """重置为默认模板"""
        self.prompt_manager.load_default_templates()
        self.prompt_manager.save_to_file()
        print("✅ 已重置为默认Prompt模板")
    
    def backup_prompts(self, backup_file: str = "prompt_backup.json"):
        """备份当前Prompt配置"""
        try:
            config = {}
            for agent_type, template in self.prompt_manager.templates.items():
                config[agent_type.value] = {
                    "system_prompt": template.system_prompt,
                    "user_prompt_template": template.user_prompt_template,
                    "response_schema": template.response_schema,
                    "temperature": template.temperature,
                    "max_tokens": template.max_tokens
                }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 已备份Prompt配置到 {backup_file}")
            
        except Exception as e:
            print(f"❌ 备份失败: {str(e)}")
    
    def restore_prompts(self, backup_file: str = "prompt_backup.json"):
        """从备份恢复Prompt配置"""
        try:
            if not os.path.exists(backup_file):
                print(f"❌ 备份文件不存在: {backup_file}")
                return
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for agent_type_str, template_config in config.items():
                agent_type = AgentType(agent_type_str)
                template = PromptTemplate(
                    system_prompt=template_config["system_prompt"],
                    user_prompt_template=template_config["user_prompt_template"],
                    response_schema=template_config.get("response_schema"),
                    temperature=template_config.get("temperature", 0.7),
                    max_tokens=template_config.get("max_tokens", 1000)
                )
                self.prompt_manager.update_template(agent_type, template)
            
            self.prompt_manager.save_to_file()
            print(f"✅ 已从 {backup_file} 恢复Prompt配置")
            
        except Exception as e:
            print(f"❌ 恢复失败: {str(e)}")

def main():
    """主函数"""
    cli = PromptManagerCLI()
    
    print("🔧 Prompt管理工具")
    print("=" * 30)
    
    while True:
        print("\n可用命令:")
        print("1. list - 列出所有Agent")
        print("2. show <agent> - 显示Agent的Prompt")
        print("3. update <agent> - 更新Agent的Prompt")
        print("4. reset - 重置为默认模板")
        print("5. backup - 备份当前配置")
        print("6. restore - 从备份恢复")
        print("7. quit - 退出")
        
        try:
            command = input("\n请输入命令: ").strip().split()
            
            if not command:
                continue
            
            if command[0] == "quit":
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
                
        except KeyboardInterrupt:
            print("\n\n👋 退出Prompt管理工具")
            break
        except Exception as e:
            print(f"❌ 执行命令时出错: {str(e)}")

if __name__ == "__main__":
    main()
