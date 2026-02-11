
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import config
from handlers.commands import router as commands_router
from services.opinion_api import OpinionAPIService
from services.db_service import DBService
from services.category_service import CategoryService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def broadcast_message(bot: Bot, subscribers: list, text: str, url: str):
    """Helper to send message to channel and all subscribers."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Trade Now 🚀", url=url))
    markup = builder.as_markup()

    if config.CHANNEL_ID:
        try:
            await bot.send_message(chat_id=config.CHANNEL_ID, text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send to channel: {e}")

    for chat_id in subscribers:
        try:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")

async def check_prices_for_spikes(spike_targets: list, bot: Bot, api_service: OpinionAPIService, db_service: DBService):
    """Background task to check prices without blocking discovery of new markets."""
    subscribers = await db_service.get_subscribers()
    if not subscribers and not config.CHANNEL_ID:
        return

    for target in spike_targets:
        try:
            target_id = target["id"]
            yes_token_id = target["yesTokenId"]
            
            if not yes_token_id:
                continue
                
            current_price = await api_service.get_token_price(yes_token_id, market_id=target.get("market_id") or target["id"])
            if current_price is not None:
                # Get price from 1 hour ago
                old_price = await db_service.get_old_price(target_id, hours=1)
                if old_price and old_price > 0:
                    change_1h = ((current_price - old_price) / old_price) * 100
                    
                    if abs(change_1h) >= config.PRICE_SPIKE_THRESHOLD:
                        last_notif = await db_service.get_last_notified_data(target_id)
                        
                        should_send = False
                        if last_notif is None:
                            should_send = True
                        else:
                            last_price = last_notif["price"]
                            last_time = last_notif["sent_at"]
                            change_since_last = ((current_price - last_price) / last_price) * 100
                            
                            if abs(change_since_last) >= config.PRICE_SPIKE_THRESHOLD:
                                should_send = True
                            elif datetime.now() - last_time > timedelta(hours=6):
                                should_send = True

                        if should_send:
                            logger.info(f"Spike alert for {target['title']}!")
                            direction = "🟩 +" if change_1h > 0 else "🟥 "
                            display_title = target["title"]
                            category_tag = CategoryService.get_category_hashtag(display_title)
                            
                            spike_message = (
                                f"⚡️ <b>Significant Change Detected!</b>\n\n"
                                f"{direction}{change_1h:.2f}% (1H) - <b>{display_title}</b>\n\n"
                                f"📊 Current Probability: {current_price*100:.1f}%\n"
                                f"💰 Volume 24h: ${target['volume24h']:,.0f}\n\n"
                                f"💡 {category_tag}"
                            )
                            trade_url = api_service.get_trade_url(target["trade_id"], is_multi=target["is_multi"])
                            await broadcast_message(bot, subscribers, spike_message, trade_url)
                            await db_service.record_spike_notification(target_id, yes_token_id, current_price)
                
                await db_service.save_price(target_id, yes_token_id, current_price)
            
            # Small delay between individual requests to maintain low RPS
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Error in background price check for {target.get('title')}: {e}")

async def monitor_markets(bot: Bot, api_service: OpinionAPIService, db_service: DBService):
    """Background task to monitor new markets and trigger background price checks."""
    logger.info("Starting market monitoring...")
    price_task = None
    
    while True:
        try:
            # 1. DISCOVERY (Fast Priority)
            markets = await api_service.get_markets()
            subscribers = await db_service.get_subscribers()
            
            if subscribers or config.CHANNEL_ID:
                child_ids_to_skip = set()
                for market in markets:
                    children = market.get("childMarkets") or []
                    for child in children:
                        child_ids_to_skip.add(str(child.get("marketId")))

                for market in markets:
                    market_id = str(market.get("marketId"))
                    created_at = market.get("createdAt", 0)
                    now_ts = datetime.now().timestamp()
                    
                    if not await db_service.is_market_processed(market_id) and market_id not in child_ids_to_skip:
                        title = market.get("marketTitle", "Unknown Market")
                        if (now_ts - created_at) > 86400: # 24 hours
                            await db_service.mark_market_as_processed(market_id, title)
                            children = market.get("childMarkets") or []
                            for child in children:
                                await db_service.mark_market_as_processed(str(child.get("marketId")), child.get("marketTitle"))
                            continue

                        logger.info(f"New market detected: {title} ({market_id})")
                        children = market.get("childMarkets") or []
                        is_multi = market.get("marketType") == 1 or len(children) > 0
                        trade_url = api_service.get_trade_url(market_id, is_multi=is_multi)
                        category_tag = CategoryService.get_category_hashtag(title)
                        
                        if children:
                            options_list = "\n".join([f"• {c.get('marketTitle')}" for c in children])
                            message_text = (
                                f"🔥 <b>{title}</b>\n\n"
                                f"<i>Multi-market:</i>\n\n"
                                f"{options_list}\n\n"
                                f"💡 Start trading on this new prediction market now.\n\n"
                                f"{category_tag}"
                            )
                            for child in children:
                                await db_service.mark_market_as_processed(str(child.get("marketId")), child.get("marketTitle"))
                        else:
                            is_hourly = "Hourly" in title
                            yes_label = (market.get("yesLabel") or "YES").upper()
                            no_label = (market.get("noLabel") or "NO").upper()
                            if is_hourly:
                                yes_icon, no_icon = "📈", "📉"
                            else:
                                yes_icon, no_icon = ("🟢", "🔵") if "UP" in yes_label else ("✅", "❌") if "YES" in yes_label else ("🔹", "🔸")
                                
                            market_type_str = "⏱ Hourly Bet" if is_hourly else "🎯 Single-market"
                            message_text = (
                                f"🔥 <b>{title}</b>\n\n"
                                f"<i>{market_type_str}:</i>\n\n"
                                f"{yes_icon}: {yes_label}\n"
                                f"{no_icon}: {no_label}\n\n"
                                f"💡 Start trading on this new prediction market now.\n\n"
                                f"{category_tag}"
                            )

                        await db_service.mark_market_as_processed(market_id, title)
                        await broadcast_message(bot, subscribers, message_text, trade_url)

                # 2. TRIGGER BACKGROUND PRICE MONITORING
                spike_targets = []
                for market in markets:
                    if market.get("resolvedAt") != 0: continue
                    children = market.get("childMarkets") or []
                    market_id = str(market.get("marketId"))
                    
                    if not children:
                        spike_targets.append({
                            "id": market_id, "title": market.get("marketTitle"),
                            "yesTokenId": market.get("yesTokenId"),
                            "volume24h": float(market.get("volume24h") or 0),
                            "trade_id": market_id, "is_multi": False
                        })
                    else:
                        parent_title = market.get("marketTitle")
                        for child in children:
                            if child.get("resolvedAt") == 0:
                                spike_targets.append({
                                    "id": str(child.get("marketId")),
                                    "title": f"{parent_title} - {child.get('marketTitle')}",
                                    "yesTokenId": child.get("yesTokenId"),
                                    "volume24h": float(child.get("volume24h") or child.get("volume") or 0),
                                    "trade_id": market_id, "market_id": str(child.get("marketId")),
                                    "is_multi": True
                                })

                # Start price check task if no previous task is running
                if price_task is None or price_task.done():
                    price_task = asyncio.create_task(check_prices_for_spikes(spike_targets, bot, api_service, db_service))
                else:
                    logger.info("Price monitoring still in progress, skipping spike update for this cycle.")

        except Exception as e:
            logger.exception(f"Error in discovery loop: {e}")
            
        await asyncio.sleep(config.POLLING_INTERVAL)

async def main():
    # Initialize bot and dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register routers
    dp.include_router(commands_router)

    # Initialize services
    api_service = OpinionAPIService()
    db_service = DBService()
    await db_service.init_db()

    # Start notification task
    asyncio.create_task(monitor_markets(bot, api_service, db_service))

    # Start polling
    logger.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
