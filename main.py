#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.
import logging

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from datetime import datetime, timedelta
from PIL import Image, ImageDraw

from secret import ADMIN_ID, BOT_TOKEN, CHANNEL_ID

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def generate_pixels(size=1, number=0, filename="pixel.png"):
    if size > 10:
        return

    if number < 0 or number > 2 ** (size * size) - 1:
        return

    numbin = bin(number)[2:].zfill(size * size)

    img = Image.new('RGB', (size, size), color='white')
    pixels = img.load()
    for i in range(size):
        for j in range(size):
            pixels[j, i] = (0, 0, 0) if numbin[j + i * size] == '1' else (255, 255, 255)

    img.resize((512, 512), Image.NEAREST).save(filename)


def gnr(context: CallbackContext) -> None:
    cur_total = context.bot_data["cur_total"]
    cur_size = context.bot_data["cur_size"]
    cur_num = context.bot_data["cur_num"]

    if cur_num > 2 ** (cur_size * cur_size) - 1:
        cur_size += 1
        context.bot_data["cur_size"] = cur_size
        cur_num = 0

    filename = "pixels.png"
    generate_pixels(size=cur_size, number=cur_num, filename=filename)

    with open(filename, "rb") as file:
        context.bot.send_photo(CHANNEL_ID, file,
                               "**Image {}**\n\- Size: {} pixels\n\- Integer: {}".format(cur_total, cur_size, cur_num),
                               parse_mode="MarkdownV2")

    context.bot_data["cur_num"] = cur_num + 1
    context.bot_data["cur_total"] = cur_total + 1


def lesgo(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == ADMIN_ID:
        try:
            cur_total, cur_size, cur_num = context.args
        except ValueError:
            cur_total, cur_size, cur_num = 1, 1, 0

        if cur_total != sum([2 ** (i ** 2) for i in range(1, cur_size)]) + cur_num + 1:
            raise ValueError("Wrong total.")

        context.bot_data["cur_total"] = cur_total
        context.bot_data["cur_size"] = cur_size
        context.bot_data["cur_num"] = cur_num
        # context.job_queue.run_daily(gnr, datetime.now().time())

        next = datetime.now().replace(microsecond=0, second=0, minute=0) + timedelta(hours=1)

        context.job_queue.run_repeating(gnr, 60 * 60, first=next)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("lesgo", lesgo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
