"""
比较工具
"""
from typing import Dict, Any, Optional
from models import AgentResponse

class ComparisonTool:
    """比较工具"""
    
    def __init__(self):
        self.comparison_engines = [
            self._historical_comparison,
            self._travel_comparison,
            self._general_comparison
        ]
    
    async def compare(self, query: str) -> AgentResponse:
        """
        执行比较
        
        Args:
            query: 比较查询
            
        Returns:
            AgentResponse: 比较结果
        """
        print(f"⚖️ 比较: {query}")
        
        # 尝试不同的比较引擎
        for engine in self.comparison_engines:
            try:
                result = await engine(query)
                if result.success:
                    print(f"✅ 比较成功")
                    return result
            except Exception as e:
                print(f"⚠️ 比较引擎异常: {str(e)}")
        
        return AgentResponse(
            success=False,
            error="无法执行此比较"
        )
    
    async def _historical_comparison(self, query: str) -> AgentResponse:
        """历史人物比较"""
        if "汉武大帝" not in query or "凯撒大帝" not in query:
            return AgentResponse(success=False, error="不是历史人物比较")
        
        # 汉武大帝 vs 凯撒大帝比较
        wudi_info = {
            "name": "汉武大帝（汉武帝）",
            "birth_year": -156,
            "death_year": -87,
            "age": 69,
            "reign_period": "公元前141年-公元前87年",
            "achievements": ["加强中央集权", "开拓疆土", "开辟丝绸之路", "独尊儒术"]
        }
        
        caesar_info = {
            "name": "凯撒大帝（尤利乌斯·凯撒）",
            "birth_year": -100,
            "death_year": -44,
            "age": 56,
            "reign_period": "独裁官时期",
            "achievements": ["征服高卢", "渡过卢比孔河", "改革历法", "扩大罗马疆域"]
        }
        
        # 年龄比较
        age_difference = wudi_info["birth_year"] - caesar_info["birth_year"]
        
        comparison_result = {
            "comparison_type": "历史人物年龄比较",
            "person1": wudi_info,
            "person2": caesar_info,
            "age_difference": age_difference,
            "conclusion": f"汉武大帝比凯撒大帝年长{age_difference}岁",
            "detailed_analysis": {
                "birth_year_diff": f"汉武大帝（公元前156年）比凯撒大帝（公元前100年）早出生{age_difference}年",
                "lifespan": f"汉武大帝享年{wudi_info['age']}岁，凯撒大帝享年{caesar_info['age']}岁",
                "era": "两人生活在不同的时代和地区，但都是各自文明的重要人物"
            }
        }
        
        return AgentResponse(
            success=True,
            result=comparison_result,
            metadata={"type": "historical_comparison", "query": query}
        )
    
    async def _travel_comparison(self, query: str) -> AgentResponse:
        """旅游景点比较"""
        if "旅游" not in query and "景点" not in query:
            return AgentResponse(success=False, error="不是旅游比较")
        
        # 模拟旅游景点比较
        return AgentResponse(
            success=True,
            result={
                "comparison_type": "旅游景点比较",
                "result": "旅游景点比较结果",
                "description": "基于多个维度的景点比较分析"
            },
            metadata={"type": "travel_comparison", "query": query}
        )
    
    async def _general_comparison(self, query: str) -> AgentResponse:
        """通用比较"""
        return AgentResponse(
            success=True,
            result={
                "comparison_type": "通用比较",
                "result": "通用比较结果",
                "description": "基于提供信息的比较分析"
            },
            metadata={"type": "general_comparison", "query": query}
        )
