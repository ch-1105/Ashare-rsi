"""
数据库模型
"""
import aiosqlite
import logging
from datetime import datetime
from config import DB_PATH
import os

logger = logging.getLogger(__name__)


async def init_db():
    """初始化数据库表"""
    # 确保 data 目录存在
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    logger.info(f"正在初始化数据库: {os.path.abspath(DB_PATH)}")
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    stock_type TEXT DEFAULT 'stock',
                    interval INTEGER DEFAULT 30,
                    rsi_period INTEGER DEFAULT 14,
                    rsi_lower REAL DEFAULT 30.0,
                    rsi_upper REAL DEFAULT 70.0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, stock_code)
                )
            """)
            await db.commit()
            logger.info("数据库初始化完成")
    except Exception as e:
        import traceback
        logger.error(f"数据库初始化失败: {e}")
        logger.error(traceback.format_exc())


class StockDAO:
    """股票数据访问对象"""
    
    @staticmethod
    async def add_stock(user_id: int, stock_code: str, stock_name: str = None,
                        stock_type: str = 'stock', interval: int = 30):
        """添加股票监控"""
        async with aiosqlite.connect(DB_PATH) as db:
            try:
                await db.execute("""
                    INSERT INTO stocks (user_id, stock_code, stock_name, stock_type, interval)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, stock_code, stock_name, stock_type, interval))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False  # 已存在
    
    @staticmethod
    async def remove_stock(user_id: int, stock_code: str):
        """移除股票监控"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                DELETE FROM stocks 
                WHERE user_id = ? AND stock_code = ?
            """, (user_id, stock_code))
            await db.commit()
    
    @staticmethod
    async def get_user_stocks(user_id: int):
        """获取用户的所有股票"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM stocks WHERE user_id = ? AND is_active = 1
            """, (user_id,)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
    
    @staticmethod
    async def get_stock_by_code(user_id: int, stock_code: str):
        """获取指定股票"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM stocks WHERE user_id = ? AND stock_code = ?
            """, (user_id, stock_code)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    @staticmethod
    async def update_stock_settings(user_id: int, stock_code: str, **kwargs):
        """更新股票设置"""
        allowed_fields = ['interval', 'stock_name', 'rsi_lower', 'rsi_upper', 'is_active']
        updates = []
        values = []
        
        for k, v in kwargs.items():
            if k in allowed_fields:
                updates.append(f"{k} = ?")
                values.append(v)
        
        if not updates:
            return
        
        values.extend([user_id, stock_code])
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(f"""
                UPDATE stocks 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND stock_code = ?
            """, values)
            await db.commit()
    
    @staticmethod
    async def get_all_active_stocks():
        """获取所有激活的股票配置"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM stocks WHERE is_active = 1
            """) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
