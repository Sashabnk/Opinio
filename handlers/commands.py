from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.markdown import hbold

from services.db_service import DBService

router = Router()
db_service = DBService()

@router.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await db_service.add_subscriber(message.chat.id)
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!\n\nI am Opinio - your analytical companion for Opinion.trade.\nYou've been subscribed to new market notifications!")

@router.message(Command("help"))
async def command_help_handler(message: types.Message) -> None:
    """
    This handler receives messages with `/help` command
    """
    await message.answer("Available commands:\n/start - Start the bot\n/help - Show this help message")
