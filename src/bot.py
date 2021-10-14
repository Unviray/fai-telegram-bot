import os
from icecream import ic

from pyrogram import Client
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from main import log, group_call, state, app, id_to_name, name_to_id


bot = Client("fai_bot",
    os.environ["API_ID"],
    os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)


@bot.on_callback_query()
def answer(client, callback_query):
    callback_query.answer(f"Button contains: '{callback_query.data}'", show_alert=True)



# bot.send_message(
#     1613056551,
#     "This is a ReplyKeyboardMarkup example",
#     reply_markup=ReplyKeyboardMarkup(
#         [
#             ["A", "B", "C", "D"],  # First row
#             ["E", "F", "G"],  # Second row
#             ["H", "I"],  # Third row
#             ["J"]  # Fourth row
#         ],
#         resize_keyboard=True  # Make the keyboard smaller
#     )
# )

bot.send_message(
    1613056551,
    "This is a InlineKeyboardMarkup example",
    reply_markup=InlineKeyboardMarkup(
        [
            [  # First row
                InlineKeyboardButton(  # Generates a callback query when pressed
                    "Button",
                    callback_data="data"
                ),
                InlineKeyboardButton(  # Opens a web URL
                    "URL",
                    url="https://docs.pyrogram.org"
                ),
            ],
            [  # Second row
                InlineKeyboardButton(  # Opens the inline interface
                    "Choose chat",
                    switch_inline_query="pyrogram"
                ),
                InlineKeyboardButton(  # Opens the inline interface in the current chat
                    "Inline here",
                    switch_inline_query_current_chat="pyrogram"
                )
            ]
        ]
    )
)


bot.run()
