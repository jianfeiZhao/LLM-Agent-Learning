"""
复杂度分析器
"""
import re
from typing import List, Dict, Any
from models import QueryComplexity

class ComplexityAnalyzer:
    """查询复杂度分析器"""
    
    def __init__(self):
        self.complexity_indicators = {
            "simple": [
                r"汉武大帝的名字",
                r"汉武帝是谁",
                r"凯撒大帝的出生日期",
                r"北京有什么景点",
                r"上海的美食"
            ],
            "complex": [
                r"比较.*?和.*?",
                r"谁更.*?",
                r"哪个.*?更好",
                r"分析.*?的.*?",
                r"制定.*?计划",
                r"规划.*?行程"
            ]
        }
    
    async def analyze(self, query: str) -> QueryComplexity:
        """
        分析查询复杂度
        
        Args:
            query: 用户查询
            
        Returns:
            QueryComplexity: 复杂度级别
        """
        # 检查简单查询模式
        for pattern in self.complexity_indicators["simple"]:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryComplexity.SIMPLE
        
        # 检查复杂查询模式
        for pattern in self.complexity_indicators["complex"]:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryComplexity.COMPLEX
        
        # 基于关键词数量判断
        complexity_score = self._calculate_complexity_score(query)
        
        if complexity_score <= 2:
            return QueryComplexity.SIMPLE
        else:
            return QueryComplexity.COMPLEX
    
    def _calculate_complexity_score(self, query: str) -> int:
        """
        计算复杂度分数
        
        Args:
            query: 用户查询
            
        Returns:
            int: 复杂度分数
        """
        score = 0
        
        # 查询长度
        if len(query) > 50:
            score += 1
        
        # 关键词数量
        keywords = ["比较", "对比", "分析", "计算", "规划", "制定", "推荐", "选择"]
        keyword_count = sum(1 for keyword in keywords if keyword in query)
        score += keyword_count
        
        # 问号数量（多个问题）
        question_count = query.count("？") + query.count("?")
        score += question_count
        
        # 连接词数量
        connectors = ["和", "与", "或者", "还是", "以及", "同时"]
        connector_count = sum(1 for connector in connectors if connector in query)
        score += connector_count
        
        return score
