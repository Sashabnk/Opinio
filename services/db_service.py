
import aiosqlite
import logging
from typing import Optional
from core.config import config
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS processed_markets (
                    market_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    chat_id INTEGER PRIMARY KEY,
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    market_id TEXT,
                    token_id TEXT,
                    price REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_price_history_market ON price_history(market_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_price_history_time ON price_history(timestamp)")
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS spike_notifications (
                    market_id TEXT,
                    token_id TEXT,
                    last_price REAL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_spike_notif_market ON spike_notifications(market_id)")
            await db.commit()

    async def add_subscriber(self, chat_id: int):
        """Add a subscriber."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
            await db.commit()

    async def get_subscribers(self) -> list[int]:
        """Get all subscriber chat IDs."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT chat_id FROM subscribers") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def is_market_processed(self, market_id: str) -> bool:
        """Check if market has already been processed (notified)."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM processed_markets WHERE market_id = ?", (market_id,)) as cursor:
                return await cursor.fetchone() is not None

    async def mark_market_as_processed(self, market_id: str, title: str = ""):
        """Save market_id to database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO processed_markets (market_id, title) VALUES (?, ?)", (market_id, title))
            await db.commit()

    async def save_price(self, market_id: str, token_id: str, price: float):
        """Save current price to history."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO price_history (market_id, token_id, price) VALUES (?, ?, ?)",
                (market_id, token_id, price)
            )
            await db.commit()

    async def get_old_price(self, market_id: str, hours: int = 1) -> Optional[float]:
        """Get the price closest to X hours ago."""
        async with aiosqlite.connect(self.db_path) as db:
            target_time = datetime.now() - timedelta(hours=hours)
            query = """
                SELECT price FROM price_history 
                WHERE market_id = ? AND timestamp <= ? 
                ORDER BY timestamp DESC LIMIT 1
            """
            async with db.execute(query, (market_id, target_time.strftime('%Y-%m-%d %H:%M:%S'))) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def should_notify_spike(self, market_id: str, hours: int = 2) -> bool:
        """Check if we already sent a spike notification for this market in the last X hours."""
        async with aiosqlite.connect(self.db_path) as db:
            limit_time = datetime.now() - timedelta(hours=hours)
            query = "SELECT 1 FROM spike_notifications WHERE market_id = ? AND sent_at > ? LIMIT 1"
            async with db.execute(query, (market_id, limit_time.strftime('%Y-%m-%d %H:%M:%S'))) as cursor:
                return await cursor.fetchone() is None

    async def record_spike_notification(self, market_id: str, token_id: str, price: float):
        """Record that a spike notification was sent."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO spike_notifications (market_id, token_id, last_price) VALUES (?, ?, ?)",
                (market_id, token_id, price)
            )
            await db.commit()

    async def get_last_notified_data(self, market_id: str) -> Optional[dict]:
        """Get the price and time of the last sent notification."""
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT last_price, sent_at FROM spike_notifications WHERE market_id = ? ORDER BY sent_at DESC LIMIT 1"
            async with db.execute(query, (market_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "price": row[0],
                        "sent_at": datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                    }
                return None
