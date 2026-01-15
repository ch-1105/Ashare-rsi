import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot 配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# 数据库路径
DB_PATH = os.getenv('DB_PATH', 'data/stocks.db')

# RSI 默认参数
RSI_PERIOD = 14
RSI_LOWER = 30.0
RSI_UPPER = 70.0

# 可用监控周期 (分钟)
# 30min, 60min, day (用 1440 表示日线)
AVAILABLE_INTERVALS = [30, 60, 1440]

# 日志级别
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# A股交易时间配置
TRADING_HOURS = [
    ('09:30', '11:30'),  # 早盘
    ('13:00', '15:00'),  # 午盘
]

# 代理配置 (可选)
PROXY_URL = os.getenv('PROXY_URL', None)
