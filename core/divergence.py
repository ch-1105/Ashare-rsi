"""
RSI 背离检测模块
检测价格与 RSI 的顶背离/底背离
"""
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DivergenceDetector:
    """RSI 背离检测器"""
    
    @staticmethod
    def find_local_extremes(data: List[float], window: int = 5) -> Tuple[List[int], List[int]]:
        """
        寻找局部极值点
        
        Args:
            data: 数据序列
            window: 检测窗口大小
            
        Returns:
            (高点索引列表, 低点索引列表)
        """
        highs = []
        lows = []
        
        for i in range(window, len(data) - window):
            # 检查是否为局部高点
            is_high = all(data[i] >= data[i-j] and data[i] >= data[i+j] for j in range(1, window + 1))
            if is_high:
                highs.append(i)
            
            # 检查是否为局部低点
            is_low = all(data[i] <= data[i-j] and data[i] <= data[i+j] for j in range(1, window + 1))
            if is_low:
                lows.append(i)
        
        return highs, lows
    
    @classmethod
    def detect_divergence(cls, prices: List[float], rsi_values: List[float], 
                          lookback: int = 20, window: int = 3) -> Optional[dict]:
        """
        检测 RSI 背离
        
        Args:
            prices: 价格序列 (收盘价)
            rsi_values: RSI 值序列
            lookback: 向前查看的周期数
            window: 极值检测窗口
            
        Returns:
            {
                'type': 'bullish' | 'bearish',  # 看涨背离 | 看跌背离
                'strength': 'strong' | 'weak',   # 强背离 | 弱背离
                'description': str
            }
            或 None (无背离)
        """
        if len(prices) < lookback or len(rsi_values) < lookback:
            return None
        
        # 取最近 lookback 个数据
        recent_prices = prices[-lookback:]
        recent_rsi = rsi_values[-lookback:]
        
        # 寻找价格和 RSI 的极值点
        price_highs, price_lows = cls.find_local_extremes(recent_prices, window)
        rsi_highs, rsi_lows = cls.find_local_extremes(recent_rsi, window)
        
        # 检测顶背离 (看跌背离): 价格创新高，RSI 未创新高
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            # 取最近的两个高点
            ph1, ph2 = price_highs[-2], price_highs[-1]
            rh1, rh2 = rsi_highs[-2], rsi_highs[-1]
            
            # 价格新高高于前高，但 RSI 新高低于前高
            if recent_prices[ph2] > recent_prices[ph1] and recent_rsi[rh2] < recent_rsi[rh1]:
                strength = 'strong' if (recent_rsi[rh1] - recent_rsi[rh2]) > 5 else 'weak'
                return {
                    'type': 'bearish',
                    'strength': strength,
                    'description': f"🔻 顶背离: 价格创新高但 RSI 走弱 ({recent_rsi[rh1]:.1f} → {recent_rsi[rh2]:.1f})"
                }
        
        # 检测底背离 (看涨背离): 价格创新低，RSI 未创新低
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            # 取最近的两个低点
            pl1, pl2 = price_lows[-2], price_lows[-1]
            rl1, rl2 = rsi_lows[-2], rsi_lows[-1]
            
            # 价格新低低于前低，但 RSI 新低高于前低
            if recent_prices[pl2] < recent_prices[pl1] and recent_rsi[rl2] > recent_rsi[rl1]:
                strength = 'strong' if (recent_rsi[rl2] - recent_rsi[rl1]) > 5 else 'weak'
                return {
                    'type': 'bullish',
                    'strength': strength,
                    'description': f"🔺 底背离: 价格创新低但 RSI 走强 ({recent_rsi[rl1]:.1f} → {recent_rsi[rl2]:.1f})"
                }
        
        return None
    
    @classmethod
    def detect_divergence_from_kline(cls, df, rsi_period: int = 14, 
                                      lookback: int = 30, window: int = 3) -> Optional[dict]:
        """
        从 K 线 DataFrame 检测背离
        
        Args:
            df: 包含 'close' 列的 DataFrame
            rsi_period: RSI 周期
            lookback: 向前查看的周期数
            window: 极值检测窗口
            
        Returns:
            背离信息字典或 None
        """
        if df is None or len(df) < lookback + rsi_period:
            return None
        
        from core.rsi import RSICalculator
        
        prices = df['close'].tolist()
        
        # 计算每个点的 RSI
        rsi_values = []
        for i in range(rsi_period + 1, len(prices) + 1):
            rsi = RSICalculator.calculate_rsi(prices[:i], period=rsi_period)
            if rsi is not None:
                rsi_values.append(rsi)
        
        if len(rsi_values) < lookback:
            return None
        
        # 对齐价格序列
        aligned_prices = prices[-(len(rsi_values)):]
        
        return cls.detect_divergence(aligned_prices, rsi_values, lookback, window)
