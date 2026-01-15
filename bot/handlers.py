"""
Telegram Bot 命令处理器
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database.models import StockDAO
from core.price import PriceService
from core.utils import format_price, format_change, validate_stock_code
from core.market_time import get_trading_status
from bot.keyboards import Keyboards
import logging

logger = logging.getLogger(__name__)

# 定义会话状态
ADD_STOCK_CODE = 1


class BotHandlers:
    def __init__(self, monitor_scheduler):
        self.monitor = monitor_scheduler
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/start 命令处理"""
        status = get_trading_status()
        
        welcome_text = (
            "📈 *A股 RSI 监控 Bot*\n\n"
            f"当前状态: {status}\n\n"
            "监控 A 股个股和 ETF 的 RSI 指标，\n"
            "当达到超买/超卖阈值时自动提醒！\n\n"
            "👇 请选择操作:"
        )
        await update.message.reply_text(
            welcome_text,
            reply_markup=Keyboards.get_main_menu(),
            parse_mode='Markdown'
        )
    
    async def list_stocks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/list 列出当前用户的监控"""
        user_id = update.effective_user.id
        stocks = await StockDAO.get_user_stocks(user_id)
        
        if not stocks:
            text = "📭 您还没有添加任何股票监控\n\n使用 /add 或点击下方按钮添加"
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text,
                    reply_markup=Keyboards.get_main_menu()
                )
            else:
                await update.message.reply_text(text, reply_markup=Keyboards.get_main_menu())
            return
        
        lines = ["📋 *您的监控列表:*\n"]
        
        for stock in stocks:
            code = stock['stock_code']
            name = stock.get('stock_name') or code
            interval = stock['interval']
            
            # 周期描述
            interval_desc = {30: '30m', 60: '60m', 1440: '日线'}.get(interval, f'{interval}m')
            
            # 获取实时数据
            price, rsi, change_pct = await self.monitor.get_latest_rsi(code, interval)
            
            price_str = format_price(price) if price else "获取中..."
            rsi_str = f"{rsi:.1f}" if rsi else "计算中"
            change_str = format_change(change_pct) if change_pct is not None else ""
            
            lines.append(
                f"• *{name}* ({code}) | {interval_desc}\n"
                f"  {price_str} {change_str} | RSI: {rsi_str}\n"
            )
        
        text = "\n".join(lines)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=Keyboards.get_main_menu(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=Keyboards.get_main_menu(),
                parse_mode='Markdown'
            )
    
    async def add_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """开始添加股票"""
        text = (
            "➕ *添加股票监控*\n\n"
            "请发送股票代码，例如:\n"
            "• `600519` - 贵州茅台\n"
            "• `000001` - 平安银行\n"
            "• `510300` - 沪深300ETF\n\n"
            "发送 /cancel 取消操作"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')
        
        return ADD_STOCK_CODE
    
    async def add_stock_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """接收股票代码并自动添加"""
        code = update.message.text.strip()
        user_id = update.effective_user.id
        
        # 验证代码格式
        if not validate_stock_code(code):
            await update.message.reply_text(
                "❌ 无效的股票代码格式\n"
                "请输入 6 位数字股票代码",
                parse_mode='Markdown'
            )
            return ADD_STOCK_CODE
        
        # 尝试获取股票信息
        msg = await update.message.reply_text("🔍 正在查询股票信息...")
        
        stock_info = PriceService.get_realtime_price(code)
        
        if not stock_info:
            await msg.edit_text(
                "⚠️ 未能获取股票信息\n"
                "请检查股票代码是否正确"
            )
            return ADD_STOCK_CODE
        
        name = stock_info.get('name', '未知')
        price = stock_info.get('price', 0)
        change_pct = stock_info.get('change_pct', 0)
        stock_type = PriceService.detect_stock_type(code)
        
        # 保存到数据库
        success = await StockDAO.add_stock(
            user_id=user_id,
            stock_code=code,
            stock_name=name,
            stock_type=stock_type,
            interval=30  # 默认 30 分钟
        )
        
        if success:
            # 刷新监控
            await self.monitor.add_monitor({
                'user_id': user_id,
                'stock_code': code,
                'stock_name': name,
                'stock_type': stock_type,
                'interval': 30
            })
            
            type_text = "ETF" if stock_type == 'etf' else "个股"
            
            await msg.edit_text(
                f"✅ *监控已开启: {name}*\n\n"
                f"📊 类型: {type_text}\n"
                f"💰 当前价: {format_price(price)}\n"
                f"📈 涨跌幅: {format_change(change_pct)}\n\n"
                f"⏱️ 监控周期: 30分钟\n"
                f"📉 RSI 阈值: 30 / 70",
                reply_markup=Keyboards.get_main_menu(),
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                "⚠️ 该股票已在您的监控列表中",
                reply_markup=Keyboards.get_main_menu()
            )
        
        return ConversationHandler.END
    
    async def cancel_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """取消添加"""
        await update.message.reply_text(
            "❌ 已取消添加操作",
            reply_markup=Keyboards.get_main_menu()
        )
        return ConversationHandler.END
    
    async def manage_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示需要管理的股票列表"""
        user_id = update.effective_user.id
        stocks = await StockDAO.get_user_stocks(user_id)
        
        if not stocks:
            text = "📭 您还没有添加任何股票\n使用 /add 添加"
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text,
                    reply_markup=Keyboards.get_main_menu()
                )
            else:
                await update.message.reply_text(text, reply_markup=Keyboards.get_main_menu())
            return
        
        text = "⚙️ *股票管理*\n\n请选择要管理的股票:"
        keyboard = Keyboards.get_stock_list_keyboard(stocks, "manage_stock")
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """通用回调处理器"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        # 主菜单命令
        if data == "cmd_start":
            status = get_trading_status()
            welcome_text = (
                "📈 *A股 RSI 监控 Bot*\n\n"
                f"当前状态: {status}\n\n"
                "监控 A 股个股和 ETF 的 RSI 指标，\n"
                "当达到超买/超卖阈值时自动提醒！\n\n"
                "👇 请选择操作:"
            )
            await query.edit_message_text(
                welcome_text,
                reply_markup=Keyboards.get_main_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "cmd_add":
            await self.add_start(update, context)
        
        elif data == "cmd_list":
            await self.list_stocks(update, context)
        
        elif data == "cmd_manage":
            await self.manage_menu(update, context)
        
        elif data == "cmd_status":
            status = get_trading_status()
            await query.edit_message_text(
                f"📊 *市场状态*\n\n{status}",
                reply_markup=Keyboards.get_main_menu(),
                parse_mode='Markdown'
            )
        
        # 管理单个股票
        elif data.startswith("manage_stock:"):
            code = data.split(":", 1)[1]
            stock = await StockDAO.get_stock_by_code(user_id, code)
            
            if stock:
                name = stock.get('stock_name') or code
                interval_desc = {30: '30分钟', 60: '60分钟', 1440: '日线'}.get(stock['interval'], f"{stock['interval']}分钟")
                
                text = (
                    f"⚙️ *管理: {name}*\n\n"
                    f"📍 代码: `{code}`\n"
                    f"⏱️ 周期: {interval_desc}\n"
                    f"📉 RSI 阈值: {stock.get('rsi_lower', 30)} / {stock.get('rsi_upper', 70)}"
                )
                await query.edit_message_text(
                    text,
                    reply_markup=Keyboards.get_stock_management_keyboard(code),
                    parse_mode='Markdown'
                )
        
        # 周期设置菜单
        elif data.startswith("menu_int:"):
            code = data.split(":", 1)[1]
            await query.edit_message_text(
                "⏱️ *选择监控周期:*",
                reply_markup=Keyboards.get_interval_keyboard(code),
                parse_mode='Markdown'
            )
        
        # 设置周期
        elif data.startswith("set_int:"):
            parts = data.split(":")
            code = parts[1]
            new_interval = int(parts[2])
            
            await StockDAO.update_stock_settings(user_id, code, interval=new_interval)
            await self.monitor.refresh_subscriptions()
            
            interval_desc = {30: '30分钟', 60: '60分钟', 1440: '日线'}.get(new_interval, f"{new_interval}分钟")
            
            await query.edit_message_text(
                f"✅ 周期已更新为 {interval_desc}",
                reply_markup=Keyboards.get_stock_management_keyboard(code)
            )
        
        # 确认删除
        elif data.startswith("confirm_del:"):
            code = data.split(":", 1)[1]
            stock = await StockDAO.get_stock_by_code(user_id, code)
            name = stock.get('stock_name') or code if stock else code
            
            await query.edit_message_text(
                f"⚠️ 确定要删除 *{name}* 的监控吗?",
                reply_markup=Keyboards.get_delete_confirmation_keyboard(code),
                parse_mode='Markdown'
            )
        
        # 执行删除
        elif data.startswith("delete_now:"):
            code = data.split(":", 1)[1]
            
            await StockDAO.remove_stock(user_id, code)
            await self.monitor.remove_monitor(user_id, code)
            
            await query.edit_message_text(
                "🗑️ 已删除该股票监控",
                reply_markup=Keyboards.get_main_menu()
            )
