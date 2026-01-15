"""
Telegram 键盘布局
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import AVAILABLE_INTERVALS


class Keyboards:
    """Telegram 键盘布局"""
    
    @staticmethod
    def get_main_menu():
        """主菜单"""
        keyboard = [
            [
                InlineKeyboardButton("➕ 添加监控", callback_data="cmd_add"),
                InlineKeyboardButton("📋 监控列表", callback_data="cmd_list"),
            ],
            [
                InlineKeyboardButton("⚙️ 管理", callback_data="cmd_manage"),
                InlineKeyboardButton("📊 市场状态", callback_data="cmd_status"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_stock_list_keyboard(stocks, action_prefix):
        """股票列表键盘"""
        keyboard = []
        
        for stock in stocks:
            code = stock['stock_code']
            name = stock.get('stock_name') or code
            interval = stock['interval']
            
            # 周期描述
            interval_desc = {30: '30m', 60: '60m', 1440: '日线'}.get(interval, f'{interval}m')
            
            text = f"{name} ({interval_desc})"
            callback_data = f"{action_prefix}:{code}"
            
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("↩️ 返回主菜单", callback_data="cmd_start")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_stock_management_keyboard(stock_code):
        """单个股票管理键盘"""
        keyboard = [
            [
                InlineKeyboardButton("⏱️ 修改周期", callback_data=f"menu_int:{stock_code}"),
            ],
            [
                InlineKeyboardButton("🗑️ 删除监控", callback_data=f"confirm_del:{stock_code}"),
            ],
            [InlineKeyboardButton("↩️ 返回列表", callback_data="cmd_manage")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_interval_keyboard(stock_code):
        """周期选择键盘"""
        interval_names = {30: '30分钟', 60: '60分钟', 1440: '日线'}
        
        keyboard = []
        for interval in AVAILABLE_INTERVALS:
            name = interval_names.get(interval, f'{interval}分钟')
            keyboard.append([
                InlineKeyboardButton(name, callback_data=f"set_int:{stock_code}:{interval}")
            ])
        
        keyboard.append([InlineKeyboardButton("↩️ 取消", callback_data=f"manage_stock:{stock_code}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_delete_confirmation_keyboard(stock_code):
        """删除确认键盘"""
        keyboard = [
            [
                InlineKeyboardButton("✅ 确认删除", callback_data=f"delete_now:{stock_code}"),
                InlineKeyboardButton("❌ 取消", callback_data=f"manage_stock:{stock_code}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
