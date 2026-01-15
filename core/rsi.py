"""
RSI 计算器
"""
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class RSICalculator:
    """RSI 指标计算器"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        使用 Wilder's Smoothing 方法计算 RSI
        
        :param prices: 价格序列 (收盘价)
        :param period: RSI 周期，默认 14
        :return: RSI 值 (0-100) 或 None
        """
        if len(prices) < period + 1:
            return None
        
        # 计算价格变化
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # 分离涨跌
        gains = [max(0, c) for c in changes]
        losses = [max(0, -c) for c in changes]
        
        # 初始平均值
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Wilder's Smoothing
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        # 计算 RS 和 RSI
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    @classmethod
    def calculate_rsi_from_kline(cls, df, period: int = 14) -> Optional[float]:
        """
        从 K 线 DataFrame 计算 RSI
        
        :param df: 包含 'close' 列的 DataFrame
        :param period: RSI 周期
        :return: 最新 RSI 值
        """
        if df is None or len(df) < period + 1:
            return None
        
        prices = df['close'].tolist()
        return cls.calculate_rsi(prices, period)
