"""
akshare 行情获取服务
"""
import akshare as ak
import pandas as pd
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PriceService:
    """A股/ETF 价格获取服务"""
    
    @staticmethod
    def detect_stock_type(code: str) -> str:
        """
        根据股票代码判断类型
        
        Returns:
            'stock' - 个股
            'etf' - ETF
            'index' - 指数
        """
        code = code.strip()
        
        # ETF 代码规则
        # 沪市 ETF: 51xxxx, 56xxxx, 58xxxx, 588xxx
        # 深市 ETF: 159xxx
        if code.startswith(('51', '56', '58', '159')):
            return 'etf'
        
        # 指数代码
        if code.startswith(('000', '399')) and len(code) == 6:
            # 需要进一步判断是指数还是股票
            # 000001 是上证指数也是平安银行
            # 这里简单处理：如果是 000 开头的6位数，默认当股票处理
            pass
        
        return 'stock'
    
    @classmethod
    def get_realtime_price(cls, code: str) -> Optional[Dict]:
        """
        获取股票/ETF 实时价格
        
        Returns:
            {
                'code': str,
                'name': str,
                'price': float,
                'change_pct': float,
                'volume': float,
                'amount': float,
                'high': float,
                'low': float,
                'open': float,
                'pre_close': float
            }
        """
        stock_type = cls.detect_stock_type(code)
        
        try:
            if stock_type == 'etf':
                return cls._get_etf_realtime(code)
            else:
                return cls._get_stock_realtime(code)
        except Exception as e:
            logger.error(f"获取实时价格失败 ({code}): {e}")
            return None
    
    @classmethod
    def _get_stock_realtime(cls, code: str) -> Optional[Dict]:
        """获取个股实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()
            
            # 查找对应股票
            row = df[df['代码'] == code]
            
            if row.empty:
                logger.warning(f"未找到股票: {code}")
                return None
            
            row = row.iloc[0]
            
            return {
                'code': code,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0) or 0),
                'change_pct': float(row.get('涨跌幅', 0) or 0),
                'volume': float(row.get('成交量', 0) or 0),
                'amount': float(row.get('成交额', 0) or 0),
                'high': float(row.get('最高', 0) or 0),
                'low': float(row.get('最低', 0) or 0),
                'open': float(row.get('今开', 0) or 0),
                'pre_close': float(row.get('昨收', 0) or 0),
            }
        except Exception as e:
            logger.error(f"获取个股行情失败 ({code}): {e}")
            return None
    
    @classmethod
    def _get_etf_realtime(cls, code: str) -> Optional[Dict]:
        """获取 ETF 实时行情"""
        try:
            df = ak.fund_etf_spot_em()
            
            # 查找对应 ETF
            row = df[df['代码'] == code]
            
            if row.empty:
                logger.warning(f"未找到 ETF: {code}")
                return None
            
            row = row.iloc[0]
            
            return {
                'code': code,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0) or 0),
                'change_pct': float(row.get('涨跌幅', 0) or 0),
                'volume': float(row.get('成交量', 0) or 0),
                'amount': float(row.get('成交额', 0) or 0),
                'high': float(row.get('最高', 0) or 0),
                'low': float(row.get('最低', 0) or 0),
                'open': float(row.get('今开', 0) or 0),
                'pre_close': float(row.get('昨收', 0) or 0),
            }
        except Exception as e:
            logger.error(f"获取 ETF 行情失败 ({code}): {e}")
            return None
    
    @classmethod
    def get_history_kline(cls, code: str, period: str = '30', count: int = 100) -> Optional[pd.DataFrame]:
        """
        获取历史 K 线数据
        
        Args:
            code: 股票/ETF 代码
            period: 周期 - '30' (30分钟), '60' (60分钟), 'daily' (日线)
            count: 获取数量
            
        Returns:
            DataFrame with columns: date, open, close, high, low, volume
        """
        stock_type = cls.detect_stock_type(code)
        
        try:
            if period == 'daily' or period == '1440':
                return cls._get_daily_kline(code, stock_type, count)
            else:
                return cls._get_minute_kline(code, stock_type, period, count)
        except Exception as e:
            logger.error(f"获取历史K线失败 ({code}, {period}): {e}")
            return None
    
    @classmethod
    def _get_daily_kline(cls, code: str, stock_type: str, count: int) -> Optional[pd.DataFrame]:
        """获取日线数据"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=count * 2)).strftime('%Y%m%d')
            
            if stock_type == 'etf':
                df = ak.fund_etf_hist_em(symbol=code, period='daily', start_date=start_date, end_date=end_date, adjust='qfq')
            else:
                df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date, adjust='qfq')
            
            if df is None or df.empty:
                return None
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })
            
            # 只保留需要的列
            df = df[['date', 'open', 'close', 'high', 'low', 'volume']].tail(count)
            
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败 ({code}): {e}")
            return None
    
    @classmethod
    def _get_minute_kline(cls, code: str, stock_type: str, period: str, count: int) -> Optional[pd.DataFrame]:
        """获取分钟线数据"""
        try:
            if stock_type == 'etf':
                df = ak.fund_etf_hist_min_em(symbol=code, period=period)
            else:
                df = ak.stock_zh_a_hist_min_em(symbol=code, period=period)
            
            if df is None or df.empty:
                return None
            
            # 标准化列名
            df = df.rename(columns={
                '时间': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })
            
            # 只保留需要的列和数量
            df = df[['date', 'open', 'close', 'high', 'low', 'volume']].tail(count)
            
            return df
        except Exception as e:
            logger.error(f"获取分钟线数据失败 ({code}, {period}min): {e}")
            return None
    
    @classmethod
    def batch_get_realtime(cls, codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取实时价格
        
        Returns:
            {code: price_info, ...}
        """
        result = {}
        
        # 分离股票和 ETF
        stock_codes = []
        etf_codes = []
        
        for code in codes:
            if cls.detect_stock_type(code) == 'etf':
                etf_codes.append(code)
            else:
                stock_codes.append(code)
        
        # 批量获取股票
        if stock_codes:
            try:
                df = ak.stock_zh_a_spot_em()
                for code in stock_codes:
                    row = df[df['代码'] == code]
                    if not row.empty:
                        row = row.iloc[0]
                        result[code] = {
                            'code': code,
                            'name': row.get('名称', ''),
                            'price': float(row.get('最新价', 0) or 0),
                            'change_pct': float(row.get('涨跌幅', 0) or 0),
                        }
            except Exception as e:
                logger.error(f"批量获取股票行情失败: {e}")
        
        # 批量获取 ETF
        if etf_codes:
            try:
                df = ak.fund_etf_spot_em()
                for code in etf_codes:
                    row = df[df['代码'] == code]
                    if not row.empty:
                        row = row.iloc[0]
                        result[code] = {
                            'code': code,
                            'name': row.get('名称', ''),
                            'price': float(row.get('最新价', 0) or 0),
                            'change_pct': float(row.get('涨跌幅', 0) or 0),
                        }
            except Exception as e:
                logger.error(f"批量获取 ETF 行情失败: {e}")
        
        return result
