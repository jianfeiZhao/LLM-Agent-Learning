"""
计算器工具
"""
import re
from typing import Dict, Any, Optional
from models import AgentResponse

class CalculatorTool:
    """计算器工具"""
    
    def __init__(self):
        self.calculators = [
            self._age_calculator,
            self._date_calculator,
            self._math_calculator
        ]
    
    async def calculate(self, query: str) -> AgentResponse:
        """
        执行计算
        
        Args:
            query: 计算查询
            
        Returns:
            AgentResponse: 计算结果
        """
        print(f"🧮 计算: {query}")
        
        # 尝试不同的计算器
        for calculator in self.calculators:
            try:
                result = await calculator(query)
                if result.success:
                    print(f"✅ 计算成功")
                    return result
            except Exception as e:
                print(f"⚠️ 计算器异常: {str(e)}")
        
        return AgentResponse(
            success=False,
            error="无法执行此计算"
        )
    
    async def _age_calculator(self, query: str) -> AgentResponse:
        """年龄计算器"""
        if "年龄" not in query and "年长" not in query:
            return AgentResponse(success=False, error="不是年龄计算")
        
        # 模拟年龄计算
        if "汉武大帝" in query:
            birth_year = -156  # 公元前156年
            death_year = -87   # 公元前87年
            age = death_year - birth_year
            
            return AgentResponse(
                success=True,
                result={
                    "person": "汉武大帝",
                    "birth_year": "公元前156年",
                    "death_year": "公元前87年",
                    "age": age,
                    "description": f"汉武大帝享年{age}岁"
                },
                metadata={"type": "age_calculation", "query": query}
            )
        
        elif "凯撒大帝" in query:
            birth_year = -100  # 公元前100年
            death_year = -44   # 公元前44年
            age = death_year - birth_year
            
            return AgentResponse(
                success=True,
                result={
                    "person": "凯撒大帝",
                    "birth_year": "公元前100年",
                    "death_year": "公元前44年",
                    "age": age,
                    "description": f"凯撒大帝享年{age}岁"
                },
                metadata={"type": "age_calculation", "query": query}
            )
        
        return AgentResponse(success=False, error="无法计算年龄")
    
    async def _date_calculator(self, query: str) -> AgentResponse:
        """日期计算器"""
        if "日期" not in query and "时间" not in query:
            return AgentResponse(success=False, error="不是日期计算")
        
        # 模拟日期计算
        return AgentResponse(
            success=True,
            result={
                "calculation": "日期计算",
                "result": "日期计算结果",
                "description": "基于历史记录的日期计算"
            },
            metadata={"type": "date_calculation", "query": query}
        )
    
    async def _math_calculator(self, query: str) -> AgentResponse:
        """数学计算器"""
        # 简单的数学表达式计算
        try:
            # 提取数字和运算符
            numbers = re.findall(r'-?\d+', query)
            operators = re.findall(r'[+\-*/]', query)
            
            if len(numbers) >= 2 and len(operators) >= 1:
                # 简单的计算逻辑
                num1 = int(numbers[0])
                num2 = int(numbers[1])
                op = operators[0]
                
                if op == '+':
                    result = num1 + num2
                elif op == '-':
                    result = num1 - num2
                elif op == '*':
                    result = num1 * num2
                elif op == '/':
                    result = num1 / num2 if num2 != 0 else "除零错误"
                else:
                    return AgentResponse(success=False, error="不支持的运算符")
                
                return AgentResponse(
                    success=True,
                    result={
                        "expression": f"{num1} {op} {num2}",
                        "result": result,
                        "description": f"计算结果: {result}"
                    },
                    metadata={"type": "math_calculation", "query": query}
                )
            
            return AgentResponse(success=False, error="无法解析数学表达式")
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"数学计算错误: {str(e)}"
            )
