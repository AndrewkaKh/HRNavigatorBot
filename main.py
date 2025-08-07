import logging
from telegram import BotCommandScopeDefault
from telegram.ext import Application

from bot.handlers import register_handlers
from bot.config import BOT_TOKEN, commands


async def setup(application: Application) -> None:
    await application.bot.set_my_commands(commands, scope=BotCommandScopeDefault())

def main():
    """
    Основная функция для запуска бота.
    """
    application = Application.builder().token(BOT_TOKEN).post_init(setup).build()

    register_handlers(application)

    logging.info("Бот запущен!")
    application.run_polling()


if __name__ == '__main__':
    main()