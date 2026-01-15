"""
监控调度器
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict

from core.price import PriceService
from core.rsi import RSICalculator
from core.market_time import is_trading_time, get_trading_status, get_next_trading_time
from core.utils import format_price, format_change
from database.models import StockDAO
from config import AVAILABLE_INTERVALS

logger = logging.getLogger(__name__)


class MonitorScheduler:
    """A股监控调度器"""
    
    def __init__(self, bot_app):
        self.bot_app = bot_app
        self.running = False
        self.tasks = []
        
        # 价格历史缓存: {(code, interval): [price1, price2, ...]}
        self.price_history: Dict[tuple, List[float]] = defaultdict(list)
        
        # 订阅配置: {(user_id, code): config_dict}
        self.subscription_configs: Dict[tuple, dict] = {}
        
        # 上次通知时间: {(user_id, code, signal_type): timestamp}
        self.last_notification: Dict[tuple, datetime] = {}
        
        # 通知冷却时间 (秒)
        self.notification_cooldown = 1800  # 30分钟，适合 A 股较长周期
    
    async def start(self):
        """启动监控"""
        if self.running:
            return
        
        self.running = True
        await self.refresh_subscriptions()
        
        # 为每个周期启动独立的监控任务
        for interval in AVAILABLE_INTERVALS:
            task = asyncio.create_task(self._monitor_loop(interval))
            self.tasks.append(task)
        
        logger.info("✅ A股监控调度器已启动")
    
    async def stop(self):
        """停止监控"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()
        logger.info("⏹ A股监控调度器已停止")
    
    async def refresh_subscriptions(self):
        """刷新订阅列表"""
        stocks = await StockDAO.get_all_active_stocks()
        
        self.subscription_configs.clear()
        
        for stock in stocks:
            key = (stock['user_id'], stock['stock_code'])
            self.subscription_configs[key] = stock
    
    async def _monitor_loop(self, interval: int):
        """
        针对特定周期的监控循环
        interval: 分钟数 (30, 60, 1440)
        """
        # 计算实际检查间隔（秒）
        # 日线在收盘后检查一次即可，分钟线按周期检查
        if interval == 1440:
            check_interval = 60  # 日线每分钟检查一次是否到收盘时间
        else:
            check_interval = interval * 60  # 分钟线按周期检查
        
        while self.running:
            try:
                # 检查是否在交易时间
                if not is_trading_time():
                    # 非交易时间，等待下一个交易时段
                    next_time = get_next_trading_time()
                    wait_seconds = (next_time - datetime.now()).total_seconds()
                    wait_seconds = min(wait_seconds, 3600)  # 最多等 1 小时再检查
                    
                    logger.info(f"[{interval}min] 非交易时间，等待 {wait_seconds:.0f} 秒")
                    await asyncio.sleep(max(60, wait_seconds))
                    continue
                
                # 获取该周期的订阅
                codes = set()
                for (user_id, code), config in self.subscription_configs.items():
                    if config['interval'] == interval:
                        codes.add(code)
                
                if codes:
                    logger.debug(f"[{interval}min] 正在检查 {len(codes)} 只股票...")
                    await self._check_stocks(list(codes), interval)
                
            except Exception as e:
                logger.error(f"[{interval}min] 监控循环出错: {e}")
            
            await asyncio.sleep(check_interval)
    
    async def _check_stocks(self, codes: List[str], interval: int):
        """检查指定股票的 RSI"""
        period_map = {30: '30', 60: '60', 1440: 'daily'}
        period = period_map.get(interval, '30')
        
        for code in codes:
            try:
                # 获取历史 K 线
                df = PriceService.get_history_kline(code, period, count=50)
                
                if df is None or len(df) < 15:
                    logger.warning(f"K线数据不足: {code}")
                    continue
                
                # 计算 RSI
                rsi_value = RSICalculator.calculate_rsi_from_kline(df)
                
                if rsi_value is None:
                    continue
                
                current_price = df['close'].iloc[-1]
                
                # 检查所有相关订阅
                for (user_id, c), config in self.subscription_configs.items():
                    if c == code and config['interval'] == interval:
                        await self._check_and_notify(config, rsi_value, current_price)
                
                # 请求间隔，避免被限流
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"检查股票失败 ({code}): {e}")
    
    async def _check_and_notify(self, config, rsi_value, current_price):
        """检查阈值并发送通知"""
        user_id = config['user_id']
        code = config['stock_code']
        name = config.get('stock_name') or code
        rsi_lower = config.get('rsi_lower', 30)
        rsi_upper = config.get('rsi_upper', 70)
        interval = config['interval']
        
        signal_type = None
        emoji = ""
        direction = ""
        
        if rsi_value <= rsi_lower:
            signal_type = "oversold"
            emoji = "🟢"
            direction = "超卖"
        elif rsi_value >= rsi_upper:
            signal_type = "overbought"
            emoji = "🔴"
            direction = "超买"
        
        if signal_type:
            # 检查通知冷却
            notify_key = (user_id, code, signal_type)
            now = datetime.now()
            last_time = self.last_notification.get(notify_key)
            
            if last_time and (now - last_time).total_seconds() < self.notification_cooldown:
                return
            
            self.last_notification[notify_key] = now
            
            # 周期描述
            interval_desc = {30: '30分钟', 60: '60分钟', 1440: '日线'}.get(interval, f'{interval}分钟')
            
            # 发送通知
            message = (
                f"{emoji} **{name}** ({code}) {direction}信号!\n\n"
                f"📊 RSI: **{rsi_value:.2f}**\n"
                f"💰 价格: {format_price(current_price)}\n"
                f"⏱️ 周期: {interval_desc}\n"
                f"⏰ {now.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            try:
                await self.bot_app.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"✉️ 已发送 {signal_type} 通知给用户 {user_id}: {name}")
            except Exception as e:
                logger.error(f"发送通知失败: {e}")
    
    async def add_monitor(self, stock_data):
        """动态添加监控"""
        await self.refresh_subscriptions()
    
    async def remove_monitor(self, user_id, stock_code):
        """动态移除监控"""
        key = (user_id, stock_code)
        if key in self.subscription_configs:
            del self.subscription_configs[key]
    
    async def get_latest_rsi(self, code: str, interval: int) -> tuple:
        """
        获取指定股票最新的价格和 RSI
        
        Returns:
            (price, rsi, change_pct)
        """
        period_map = {30: '30', 60: '60', 1440: 'daily'}
        period = period_map.get(interval, '30')
        
        try:
            # 获取历史 K 线
            df = PriceService.get_history_kline(code, period, count=50)
            
            if df is not None and len(df) >= 15:
                rsi = RSICalculator.calculate_rsi_from_kline(df)
                price = df['close'].iloc[-1]
                
                # 获取涨跌幅
                if len(df) >= 2:
                    pre_close = df['close'].iloc[-2]
                    change_pct = (price - pre_close) / pre_close * 100 if pre_close else 0
                else:
                    change_pct = 0
                
                return price, rsi, change_pct
        except Exception as e:
            logger.error(f"获取最新 RSI 失败 ({code}): {e}")
        
        return None, None, None
