"""
多周期共振检测模块
当多个周期的 RSI 同时处于超买/超卖区间时，信号更可靠
"""
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class ResonanceDetector:
    """多周期共振检测器"""
    
    @staticmethod
    def check_resonance(rsi_by_interval: Dict[int, float], 
                        lower_threshold: float = 30.0,
                        upper_threshold: float = 70.0) -> Optional[dict]:
        """
        检查多周期 RSI 共振
        
        Args:
            rsi_by_interval: {周期: RSI值} 字典，如 {30: 28.5, 60: 32.1, 1440: 25.3}
            lower_threshold: 超卖阈值
            upper_threshold: 超买阈值
            
        Returns:
            {
                'type': 'oversold' | 'overbought',
                'strength': int,  # 共振周期数量
                'intervals': List[int],  # 参与共振的周期
                'avg_rsi': float,  # 平均 RSI
                'description': str
            }
            或 None (无共振)
        """
        if not rsi_by_interval or len(rsi_by_interval) < 2:
            return None
        
        interval_names = {30: '30分钟', 60: '60分钟', 1440: '日线'}
        
        # 检查超卖共振
        oversold_intervals = [i for i, rsi in rsi_by_interval.items() if rsi <= lower_threshold]
        if len(oversold_intervals) >= 2:
            avg_rsi = sum(rsi_by_interval[i] for i in oversold_intervals) / len(oversold_intervals)
            interval_names_list = [interval_names.get(i, f'{i}分钟') for i in oversold_intervals]
            
            return {
                'type': 'oversold',
                'strength': len(oversold_intervals),
                'intervals': oversold_intervals,
                'avg_rsi': avg_rsi,
                'description': f"🎯 多周期共振超卖! {' + '.join(interval_names_list)} 均处于超卖区"
            }
        
        # 检查超买共振
        overbought_intervals = [i for i, rsi in rsi_by_interval.items() if rsi >= upper_threshold]
        if len(overbought_intervals) >= 2:
            avg_rsi = sum(rsi_by_interval[i] for i in overbought_intervals) / len(overbought_intervals)
            interval_names_list = [interval_names.get(i, f'{i}分钟') for i in overbought_intervals]
            
            return {
                'type': 'overbought',
                'strength': len(overbought_intervals),
                'intervals': overbought_intervals,
                'avg_rsi': avg_rsi,
                'description': f"🎯 多周期共振超买! {' + '.join(interval_names_list)} 均处于超买区"
            }
        
        return None
    
    @classmethod
    async def get_multi_period_rsi(cls, code: str, intervals: List[int] = None) -> Dict[int, float]:
        """
        获取多个周期的 RSI 值
        
        Args:
            code: 股票代码
            intervals: 要检查的周期列表，默认 [30, 60, 1440]
            
        Returns:
            {周期: RSI值} 字典
        """
        from core.price import PriceService
        from core.rsi import RSICalculator
        
        if intervals is None:
            intervals = [30, 60, 1440]
        
        period_map = {30: '30', 60: '60', 1440: 'daily'}
        result = {}
        
        for interval in intervals:
            try:
                period = period_map.get(interval, '30')
                df = PriceService.get_history_kline(code, period, count=50)
                
                if df is not None and len(df) >= 15:
                    rsi = RSICalculator.calculate_rsi_from_kline(df)
                    if rsi is not None:
                        result[interval] = rsi
            except Exception as e:
                logger.warning(f"获取 {code} {interval}min RSI 失败: {e}")
        
        return result
