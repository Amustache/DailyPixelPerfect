import logging
import os
import random
from datetime import datetime, timedelta

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from dailypixelperfect.secret import BOT_TOKEN, CHANNEL_ID, ADMIN_ID
from dailypixelperfect.utilities import BASEDIR, escape_for_telegram, generate_pixels

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

with open(os.path.join(BASEDIR, "blabla"), "r") as f:
    help_message = f.read()


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        help_message,
        parse_mode="MarkdownV2",
    )
    return


async def generate_send_delete(number: int, size: int, dest: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    path = os.path.join(BASEDIR, "generated", f"{dest}.png")

    try:
        generate_pixels(size=size, number=number, filename=path)
        total = sum([2 ** (i ** 2) for i in range(1, int(size))]) + int(number) + 1
    except ValueError as e:
        await context.bot.send_message(
            dest,
            f"Could not generate image: {e}.",
        )
        return

    with open(path, "rb") as p:
        await context.bot.send_photo(
            dest,
            p,
            caption=f"Image {total}\nSize: {size} pixels\nInteger: {number}",
        )

    os.remove(path)

    return


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        size, number = context.args
        size = int(size)
        number = int(number)
    except ValueError:
        await update.message.reply_text(
            "Could not generate image: parameters are wrong."
        )
        return

    return await generate_send_delete(number, size, update.effective_user.id, context)


async def generate_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    size = random.randint(1, 10)
    number = random.randint(0, 2 ** (size * size) - 1)

    return await generate_send_delete(number, size, update.effective_user.id, context)

async def generate_each_hour(context: ContextTypes.DEFAULT_TYPE) -> None:
    # Take parameters for current run
    size = context.bot_data["cur_size"]
    number = context.bot_data["cur_num"]

    # Increment for next run
    if number + 1 > 2 ** (size * size) - 1:
        context.bot_data["cur_size"] = size + 1
        context.bot_data["cur_num"] = 0
    else:
        context.bot_data["cur_num"] = number + 1

    return await generate_send_delete(number, size, CHANNEL_ID, context)

async def channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not admin.")
        return

    try:
        size, number = context.args
        size = int(size)
        number = int(number)
    except ValueError:
        await update.message.reply_text(
            "Could not start channel: parameters are wrong."
        )
        return

    context.bot_data["cur_size"] = size
    context.bot_data["cur_num"] = number

    next_run = datetime.now().replace(microsecond=0, second=0, minute=0) + timedelta(hours=1)

    context.job_queue.run_repeating(generate_each_hour, 60 * 60, first=next_run)

    await update.message.reply_text(f"Started channel. Next run: {next_run.isoformat()}")

    return

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("generate", generate))
    application.add_handler(CommandHandler("random", generate_random))
    application.add_handler(CommandHandler("channel_start", channel_start))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
