"""
A股交易时间判断模块
"""
from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)

# A股交易时段
MORNING_START = time(9, 30)
MORNING_END = time(11, 30)
AFTERNOON_START = time(13, 0)
AFTERNOON_END = time(15, 0)

# 2024-2025 中国法定节假日 (手动维护，可后续接入 API)
HOLIDAYS = {
    # 2024
    '2024-01-01',  # 元旦
    '2024-02-10', '2024-02-11', '2024-02-12', '2024-02-13', '2024-02-14', '2024-02-15', '2024-02-16', '2024-02-17',  # 春节
    '2024-04-04', '2024-04-05', '2024-04-06',  # 清明节
    '2024-05-01', '2024-05-02', '2024-05-03', '2024-05-04', '2024-05-05',  # 劳动节
    '2024-06-08', '2024-06-09', '2024-06-10',  # 端午节
    '2024-09-15', '2024-09-16', '2024-09-17',  # 中秋节
    '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-04', '2024-10-05', '2024-10-06', '2024-10-07',  # 国庆节
    # 2025
    '2025-01-01',  # 元旦
    '2025-01-28', '2025-01-29', '2025-01-30', '2025-01-31', '2025-02-01', '2025-02-02', '2025-02-03', '2025-02-04',  # 春节
    '2025-04-04', '2025-04-05', '2025-04-06',  # 清明节
    '2025-05-01', '2025-05-02', '2025-05-03', '2025-05-04', '2025-05-05',  # 劳动节
    '2025-05-31', '2025-06-01', '2025-06-02',  # 端午节
    '2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05', '2025-10-06', '2025-10-07',  # 国庆节
    # 2026
    '2026-01-01', '2026-01-02',  # 元旦
    '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22', '2026-02-23',  # 春节
}


def is_trading_day(dt: datetime = None) -> bool:
    """
    判断给定日期是否为交易日
    排除周末和法定节假日
    """
    if dt is None:
        dt = datetime.now()
    
    # 周末不交易
    if dt.weekday() >= 5:
        return False
    
    # 节假日不交易
    date_str = dt.strftime('%Y-%m-%d')
    if date_str in HOLIDAYS:
        return False
    
    return True


def is_trading_time(dt: datetime = None) -> bool:
    """
    判断当前是否在交易时段
    """
    if dt is None:
        dt = datetime.now()
    
    # 首先检查是否为交易日
    if not is_trading_day(dt):
        return False
    
    current_time = dt.time()
    
    # 检查是否在早盘或午盘时段
    in_morning = MORNING_START <= current_time <= MORNING_END
    in_afternoon = AFTERNOON_START <= current_time <= AFTERNOON_END
    
    return in_morning or in_afternoon


def get_next_trading_time(dt: datetime = None) -> datetime:
    """
    获取下一个交易时段的开始时间
    """
    if dt is None:
        dt = datetime.now()
    
    current_time = dt.time()
    
    # 如果今天是交易日
    if is_trading_day(dt):
        # 早盘前
        if current_time < MORNING_START:
            return dt.replace(hour=9, minute=30, second=0, microsecond=0)
        # 午休期间
        elif MORNING_END < current_time < AFTERNOON_START:
            return dt.replace(hour=13, minute=0, second=0, microsecond=0)
    
    # 需要找下一个交易日
    from datetime import timedelta
    next_day = dt + timedelta(days=1)
    while not is_trading_day(next_day):
        next_day += timedelta(days=1)
    
    return next_day.replace(hour=9, minute=30, second=0, microsecond=0)


def get_trading_status() -> str:
    """
    获取当前交易状态描述
    """
    now = datetime.now()
    
    if not is_trading_day(now):
        if now.weekday() >= 5:
            return "⏸️ 周末休市"
        else:
            return "⏸️ 节假日休市"
    
    current_time = now.time()
    
    if current_time < MORNING_START:
        return "⏳ 盘前等待"
    elif MORNING_START <= current_time <= MORNING_END:
        return "🟢 早盘交易中"
    elif MORNING_END < current_time < AFTERNOON_START:
        return "⏸️ 午间休市"
    elif AFTERNOON_START <= current_time <= AFTERNOON_END:
        return "🟢 午盘交易中"
    else:
        return "🔴 已收盘"
