"""
A股 RSI 监控 Telegram Bot 入口
"""
import asyncio
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

from config import TELEGRAM_BOT_TOKEN, LOG_LEVEL, PROXY_URL
from database.models import init_db
from core.monitor import MonitorScheduler
from bot.handlers import BotHandlers, ADD_STOCK_CODE

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL, logging.INFO)
)
# 降低 httpx 等库的日志级别，避免请求日志刷屏
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def post_init(app: Application):
    """应用初始化后的钩子"""
    # 设置 Bot 菜单命令
    from telegram import BotCommand
    commands = [
        BotCommand("start", "🏠 显示主菜单"),
        BotCommand("add", "➕ 添加股票监控"),
        BotCommand("list", "📋 查看所有监控"),
        BotCommand("manage", "⚙️ 管理监控股票"),
        BotCommand("status", "📊 查看市场状态"),
    ]
    await app.bot.set_my_commands(commands)
    
    # 初始化数据库
    await init_db()
    
    # 启动监控器
    monitor = app.bot_data.get('monitor')
    if monitor:
        await monitor.start()


async def post_shutdown(app: Application):
    """应用关闭前的钩子"""
    monitor = app.bot_data.get('monitor')
    if monitor:
        await monitor.stop()


def main():
    """主函数"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ 未设置 TELEGRAM_BOT_TOKEN 环境变量")
        return
    
    # 创建应用
    builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    
    # 配置代理 (如果需要)
    if PROXY_URL:
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(proxy=PROXY_URL)
        builder = builder.request(request)
    
    app = builder.build()
    
    # 创建监控器
    monitor = MonitorScheduler(app)
    app.bot_data['monitor'] = monitor
    
    # 创建处理器
    handlers = BotHandlers(monitor)
    
    # 注册添加股票的会话处理器
    add_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", handlers.add_start),
            CallbackQueryHandler(handlers.add_start, pattern="^cmd_add$")
        ],
        states={
            ADD_STOCK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.add_stock_code)],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel_add)],
    )
    
    # 注册处理器
    app.add_handler(add_conv_handler)
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("list", handlers.list_stocks))
    app.add_handler(CommandHandler("manage", handlers.manage_menu))
    app.add_handler(CallbackQueryHandler(handlers.handle_callback))
    
    # 注册生命周期钩子
    app.post_init = post_init
    app.post_shutdown = post_shutdown
    
    # 启动
    logger.info("🚀 A股 RSI 监控 Bot 启动中...")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"发生未捕获异常: {e}")
        raise
