"""
工具函数
"""


def format_price(price: float) -> str:
    """格式化价格显示"""
    if price is None:
        return "N/A"
    return f"¥{price:.2f}"


def format_change(change_pct: float) -> str:
    """格式化涨跌幅显示"""
    if change_pct is None:
        return "N/A"
    
    emoji = "🔴" if change_pct < 0 else "🟢" if change_pct > 0 else "⚪"
    return f"{emoji} {change_pct:+.2f}%"


def format_volume(volume: float) -> str:
    """格式化成交量显示"""
    if volume is None or volume == 0:
        return "N/A"
    
    if volume >= 100_000_000:
        return f"{volume / 100_000_000:.2f}亿手"
    elif volume >= 10_000:
        return f"{volume / 10_000:.2f}万手"
    else:
        return f"{volume:.0f}手"


def format_amount(amount: float) -> str:
    """格式化成交额显示"""
    if amount is None or amount == 0:
        return "N/A"
    
    if amount >= 100_000_000:
        return f"¥{amount / 100_000_000:.2f}亿"
    elif amount >= 10_000:
        return f"¥{amount / 10_000:.2f}万"
    else:
        return f"¥{amount:.2f}"


def validate_stock_code(code: str) -> bool:
    """
    验证股票代码格式
    
    支持:
    - 沪市主板: 600xxx, 601xxx, 603xxx, 605xxx
    - 深市主板: 000xxx, 001xxx
    - 创业板: 300xxx, 301xxx
    - 科创板: 688xxx, 689xxx
    - 北交所: 8xxxxx, 4xxxxx
    - ETF: 51xxxx, 56xxxx, 159xxx
    """
    if not code or not code.isdigit() or len(code) != 6:
        return False
    
    # 有效的前缀
    valid_prefixes = (
        '600', '601', '603', '605',  # 沪市主板
        '000', '001', '002', '003',  # 深市主板
        '300', '301',  # 创业板
        '688', '689',  # 科创板
        '8', '4',  # 北交所
        '51', '52', '56', '58', '159',  # ETF
    )
    
    return code.startswith(valid_prefixes)
