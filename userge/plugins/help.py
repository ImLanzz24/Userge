# pylint: disable=missing-module-docstring
#
# Copyright (C) 2020-2021 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/UsergeTeam/Userge/blob/master/LICENSE >
#
# All rights reserved.

from math import ceil
from uuid import uuid4
from typing import List, Callable, Dict, Union, Any

from pyrogram import filters
from pyrogram.types import (
    InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, InlineQuery)
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified, MessageIdInvalid

from userge import userge, Message, Config, get_collection
from userge.utils import is_command

_CATEGORY = {
    'admin': '👨‍✈️',
    'fun': '🎨',
    'misc': '⚙️',
    'tools': '🧰',
    'utils': '🗂',
    'unofficial': '🃏',
    'temp': '♻️',
    'custom': '👨',
    'plugins': '💎'
}
SAVED_SETTINGS = get_collection("CONFIGS")
PRVT_MSGS = {}


async def _init() -> None:
    data = await SAVED_SETTINGS.find_one({'_id': 'CURRENT_CLIENT'})
    if data:
        Config.USE_USER_FOR_CLIENT_CHECKS = bool(data['is_user'])


@userge.on_cmd("help", about={'header': "Guide to use USERGE commands"}, allow_channels=False)
async def helpme(message: Message) -> None:  # pylint: disable=missing-function-docstring
    plugins = userge.manager.enabled_plugins
    if not message.input_str:
        out_str = f"""⚒ <b><u>(<code>{len(plugins)}</code>) PLUGIN YG TERSEDIA TOD</u></b>\n\n"""
        cat_plugins = userge.manager.get_plugins()
        for cat in sorted(cat_plugins):
            if cat == "plugins":
                continue
            out_str += (f"    {_CATEGORY.get(cat, '📁')} <b>{cat}</b> "
                        f"(<code>{len(cat_plugins[cat])}</code>) :   <code>"
                        + "</code>    <code>".join(sorted(cat_plugins[cat])) + "</code>\n\n")
        out_str += f"""📕 <b>Usage:</b>  <code>{Config.CMD_TRIGGER}help [plugin_name]</code>"""
    else:
        key = message.input_str
        if (not key.startswith(Config.CMD_TRIGGER)
                and key in plugins
                and (len(plugins[key].enabled_commands) > 1
                     or plugins[key].enabled_commands[0].name.lstrip(Config.CMD_TRIGGER) != key)):
            commands = plugins[key].enabled_commands
            out_str = f"""⚔ <b><u>(<code>{len(commands)}</code>) Command(s) Available</u></b>

🔧 <b>Plugin:</b>  <code>{key}</code>
📘 <b>Doc:</b>  <code>{plugins[key].doc}</code>\n\n"""
            for i, cmd in enumerate(commands, start=1):
                out_str += (f"    🤖 <b>cmd(<code>{i}</code>):</b>  <code>{cmd.name}</code>\n"
                            f"    📚 <b>info:</b>  <i>{cmd.doc}</i>\n\n")
            out_str += f"""📕 <b>Gunakan :</b>  <code>{Config.CMD_TRIGGER}help [command_name]</code>"""
        else:
            commands = userge.manager.enabled_commands
            key = key.lstrip(Config.CMD_TRIGGER)
            key_ = Config.CMD_TRIGGER + key
            if key in commands:
                out_str = f"<code>{key}</code>\n\n{commands[key].about}"
            elif key_ in commands:
                out_str = f"<code>{key_}</code>\n\n{commands[key_].about}"
            else:
                out_str = f"<i>No Module or Command Found for</i>: <code>{message.input_str}</code>"
    await message.edit(out_str, del_in=0, parse_mode='html', disable_web_page_preview=True)

if userge.has_bot:
    def check_owner(func):
        async def wrapper(_, c_q: CallbackQuery):
            if c_q.from_user and c_q.from_user.id in Config.OWNER_ID:
                try:
                    await func(c_q)
                except MessageNotModified:
                    await c_q.answer("Nothing Found to Refresh 🤷‍♂️", show_alert=True)
                except MessageIdInvalid:
                    await c_q.answer("Sorry, I Don't Have Permissions to edit this 😔",
                                     show_alert=True)
            else:
                user_dict = await userge.bot.get_user_dict(Config.OWNER_ID[0])
                await c_q.answer(
                    f"Only {user_dict['flname']} Can Access this...! Build Your Own @qunthuul🤘",
                    show_alert=True)
        return wrapper

    @userge.bot.on_message(
        filters.private & filters.user(list(Config.OWNER_ID)) & filters.command("start")
    )
    async def pm_help_handler(_, msg: Message):
        cmd = msg.command[1] if len(msg.command) > 1 else ''
        if not cmd:
            return
        commands = userge.manager.enabled_commands
        key = Config.CMD_TRIGGER + cmd
        key_ = Config.SUDO_TRIGGER + cmd
        if cmd in commands:
            out_str = f"<code>{cmd}</code>\n\n{commands[cmd].about}"
        elif key in commands:
            out_str = f"<code>{key}</code>\n\n{commands[key].about}"
        elif key_ in commands:
            out_str = f"<code>{key_}</code>\n\n{commands[key_].about}"
        else:
            out_str = f"<i>No Command Found for</i>: <code>{cmd}</code>"
        await msg.reply(out_str, parse_mode='html', disable_web_page_preview=True)

    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"\((.+)\)(next|prev)\((\d+)\)"))
    @check_owner
    async def callback_next_prev(callback_query: CallbackQuery):
        cur_pos = str(callback_query.matches[0].group(1))
        n_or_p = str(callback_query.matches[0].group(2))
        p_num = int(callback_query.matches[0].group(3))
        p_num = p_num + 1 if n_or_p == "next" else p_num - 1
        pos_list = cur_pos.split('|')
        if len(pos_list) == 1:
            buttons = parse_buttons(p_num, cur_pos,
                                    lambda x: f"{_CATEGORY.get(x, '📁')} {x}",
                                    userge.manager.get_all_plugins())
        elif len(pos_list) == 2:
            buttons = parse_buttons(p_num, cur_pos,
                                    lambda x: f"🗃 {x}",
                                    userge.manager.get_all_plugins()[pos_list[-1]])
        elif len(pos_list) == 3:
            _, buttons = plugin_data(cur_pos, p_num)
        await callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons))

    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"back\((.+)\)"))
    @check_owner
    async def callback_back(callback_query: CallbackQuery):
        cur_pos = str(callback_query.matches[0].group(1))
        pos_list = cur_pos.split('|')
        if len(pos_list) == 1:
            await callback_query.answer("you are in main menu", show_alert=True)
            return
        if len(pos_list) == 2:
            text = "🖥 **FadhlanBots Main Menu** 🖥"
            buttons = main_menu_buttons()
        elif len(pos_list) == 3:
            text, buttons = category_data(cur_pos)
        elif len(pos_list) == 4:
            text, buttons = plugin_data(cur_pos)
        await callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(buttons))

    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"enter\((.+)\)"))
    @check_owner
    async def callback_enter(callback_query: CallbackQuery):
        cur_pos = str(callback_query.matches[0].group(1))
        pos_list = cur_pos.split('|')
        if len(pos_list) == 2:
            text, buttons = category_data(cur_pos)
        elif len(pos_list) == 3:
            text, buttons = plugin_data(cur_pos)
        elif len(pos_list) == 4:
            text, buttons = filter_data(cur_pos)
        await callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(buttons))

    @userge.bot.on_callback_query(
        filters=filters.regex(pattern=r"((?:un)?load|(?:en|dis)able)\((.+)\)"))
    @check_owner
    async def callback_manage(callback_query: CallbackQuery):
        task = str(callback_query.matches[0].group(1))
        cur_pos = str(callback_query.matches[0].group(2))
        pos_list = cur_pos.split('|')
        if len(pos_list) == 4:
            if is_filter(pos_list[-1]):
                flt = userge.manager.filters[pos_list[-1]]
            else:
                flt = userge.manager.commands[pos_list[-1]]
            await getattr(flt, task)()
            text, buttons = filter_data(cur_pos)
        else:
            plg = userge.manager.plugins[pos_list[-1]]
            await getattr(plg, task)()
            text, buttons = plugin_data(cur_pos)
        await callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(buttons))

    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"^mm$"))
    @check_owner
    async def callback_mm(callback_query: CallbackQuery):
        await callback_query.edit_message_text(
            "🖥 **FadhlanBot Main Menu** 🖥", reply_markup=InlineKeyboardMarkup(main_menu_buttons()))

    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"^chgclnt$"))
    @check_owner
    async def callback_chgclnt(callback_query: CallbackQuery):
        if not userge.dual_mode:
            return await callback_query.answer(
                "you using [BOT MODE], can't change client.", show_alert=True)
        if Config.USE_USER_FOR_CLIENT_CHECKS:
            Config.USE_USER_FOR_CLIENT_CHECKS = False
        else:
            Config.USE_USER_FOR_CLIENT_CHECKS = True
        await SAVED_SETTINGS.update_one({'_id': 'CURRENT_CLIENT'},
                                        {"$set": {'is_user': Config.USE_USER_FOR_CLIENT_CHECKS}},
                                        upsert=True)
        await callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(main_menu_buttons()))

    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"refresh\((.+)\)"))
    @check_owner
    async def callback_exit(callback_query: CallbackQuery):
        cur_pos = str(callback_query.matches[0].group(1))
        pos_list = cur_pos.split('|')
        if len(pos_list) == 4:
            text, buttons = filter_data(cur_pos)
        else:
            text, buttons = plugin_data(cur_pos)
        await callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(buttons))

    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"prvtmsg\((.+)\)"))
    async def prvt_msg(_, c_q: CallbackQuery):
        msg_id = str(c_q.matches[0].group(1))
        if msg_id not in PRVT_MSGS:
            await c_q.answer("message now outdated !", show_alert=True)
            return
        user_id, flname, msg = PRVT_MSGS[msg_id]
        if c_q.from_user.id == user_id or c_q.from_user.id in Config.OWNER_ID:
            await c_q.answer(msg, show_alert=True)
        else:
            await c_q.answer(
                f"Only {flname} can see this Private Msg... 😔", show_alert=True)

    def is_filter(name: str) -> bool:
        split_ = name.split('.')
        return bool(split_[0] and len(split_) == 2)

    def parse_buttons(page_num: int,
                      cur_pos: str,
                      func: Callable[[str], str],
                      data: Union[List[str], Dict[str, Any]],
                      rows: int = 3):
        buttons = [InlineKeyboardButton(
            func(x), callback_data=f"enter({cur_pos}|{x})".encode()) for x in sorted(data)]
        pairs = list(map(list, zip(buttons[::2], buttons[1::2])))
        if len(buttons) % 2 == 1:
            pairs.append([buttons[-1]])
        max_pages = ceil(len(pairs) / rows)
        current_page = page_num % max_pages
        if len(pairs) > rows:
            pairs = pairs[current_page*rows:(current_page + 1)*rows] + [
                [
                    InlineKeyboardButton(
                        "⏪ Previous", callback_data=f"({cur_pos})prev({current_page})".encode()),
                    InlineKeyboardButton(
                        "⏩ Next", callback_data=f"({cur_pos})next({current_page})".encode())],
            ]
        pairs += default_buttons(cur_pos)
        return pairs

    def main_menu_buttons():
        return parse_buttons(0, "mm",
                             lambda x: f"{_CATEGORY.get(x, '📁')} {x}",
                             userge.manager.get_all_plugins())

    def default_buttons(cur_pos: str):
        tmp_btns = []
        if cur_pos != "mm":
            tmp_btns.append(InlineKeyboardButton(
                "⬅ Back", callback_data=f"back({cur_pos})".encode()))
            if len(cur_pos.split('|')) > 2:
                tmp_btns.append(InlineKeyboardButton(
                    "🖥 Main Menu", callback_data="mm".encode()))
                tmp_btns.append(InlineKeyboardButton(
                    "🔄 Refresh", callback_data=f"refresh({cur_pos})".encode()))
        elif userge.dual_mode:
            cur_clnt = "👲 USER" if Config.USE_USER_FOR_CLIENT_CHECKS else "🤖 BOT"
            tmp_btns.append(InlineKeyboardButton(
                f"🔩 Client for Checks and Sudos : {cur_clnt}", callback_data="chgclnt".encode()))
        return [tmp_btns]

    def category_data(cur_pos: str):
        pos_list = cur_pos.split('|')
        plugins = userge.manager.get_all_plugins()[pos_list[1]]
        text = (f"**(`{len(plugins)}`) Plugin(s) Under : "
                f"`{_CATEGORY.get(pos_list[1], '📁')} {pos_list[1]}` 🎭 Category**")
        buttons = parse_buttons(0, '|'.join(pos_list[:2]),
                                lambda x: f"🗃 {x}",
                                plugins)
        return text, buttons

    def plugin_data(cur_pos: str, p_num: int = 0):
        pos_list = cur_pos.split('|')
        plg = userge.manager.plugins[pos_list[2]]
        text = f"""🗃 **--Plugin Status--** 🗃

🎭 **Category** : `{pos_list[1]}`
🔖 **Name** : `{plg.name}`
📝 **Doc** : `{plg.doc}`
⚔ **Commands** : `{len(plg.commands)}`
⚖ **Filters** : `{len(plg.filters)}`
✅ **Loaded** : `{plg.is_loaded}`
➕ **Enabled** : `{plg.is_enabled}`
"""
        tmp_btns = []
        if plg.is_loaded:
            tmp_btns.append(InlineKeyboardButton(
                "❎ Unload", callback_data=f"unload({'|'.join(pos_list[:3])})".encode()))
        else:
            tmp_btns.append(InlineKeyboardButton(
                "✅ Load", callback_data=f"load({'|'.join(pos_list[:3])})".encode()))
        if plg.is_enabled:
            tmp_btns.append(InlineKeyboardButton(
                "➖ Disable", callback_data=f"disable({'|'.join(pos_list[:3])})".encode()))
        else:
            tmp_btns.append(InlineKeyboardButton(
                "➕ Enable", callback_data=f"enable({'|'.join(pos_list[:3])})".encode()))
        buttons = parse_buttons(p_num, '|'.join(pos_list[:3]),
                                lambda x: f"⚖ {x}" if is_filter(x) else f"⚔ {x}",
                                (flt.name for flt in plg.commands + plg.filters))
        buttons = buttons[:-1] + [tmp_btns] + [buttons[-1]]
        return text, buttons

    def filter_data(cur_pos: str):
        pos_list = cur_pos.split('|')
        plg = userge.manager.plugins[pos_list[2]]
        flts = {flt.name: flt for flt in plg.commands + plg.filters}
        flt = flts[pos_list[-1]]
        flt_data = f"""
🔖 **Name** : `{flt.name}`
📝 **Doc** : `{flt.doc}`
🤖 **Via Bot** : `{flt.allow_via_bot}`
✅ **Loaded** : `{flt.is_loaded}`
➕ **Enabled** : `{flt.is_enabled}`"""
        if hasattr(flt, 'about'):
            text = f"""⚔ **--Command Status--**
{flt_data}
{flt.about}
"""
        else:
            text = f"""⚖ **--Filter Status--** ⚖
{flt_data}
"""
        buttons = default_buttons(cur_pos)
        tmp_btns = []
        if flt.is_loaded:
            tmp_btns.append(InlineKeyboardButton(
                "❎ Unload", callback_data=f"unload({cur_pos})".encode()))
        else:
            tmp_btns.append(InlineKeyboardButton(
                "✅ Load", callback_data=f"load({cur_pos})".encode()))
        if flt.is_enabled:
            tmp_btns.append(InlineKeyboardButton(
                "➖ Disable", callback_data=f"disable({cur_pos})".encode()))
        else:
            tmp_btns.append(InlineKeyboardButton(
                "➕ Enable", callback_data=f"enable({cur_pos})".encode()))
        buttons = [tmp_btns] + buttons
        return text, buttons

    @userge.bot.on_inline_query()
    async def inline_answer(_, inline_query: InlineQuery):
        results = [
            InlineQueryResultArticle(
                id=uuid4(),
                title="Repo",
                input_message_content=InputTextMessageContent(
                    "**Here's how to setup FadhlanBot** 😎"
                ),
                url="https://github.com/ImLanzz24/Userge",
                description="Setup Your Own",
                thumb_url="https://i.ibb.co/2SMX7vV/20211010-112307.jpg",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🧰  Mwehehe Boy",
                                url="https://t.me/qunthuul"),
                            InlineKeyboardButton(
                                "🖥 D Userge",
                                url="https://t.me/qunthuul")
                        ]
                    ]
                )
            )
        ]
        if inline_query.from_user and inline_query.from_user.id in Config.OWNER_ID:
            results.append(
                InlineQueryResultArticle(
                    id=uuid4(),
                    title="Main Menu",
                    input_message_content=InputTextMessageContent(
                        "🖥 **FadhlanBotMain Menu** 🖥"
                    ),
                    url="https://t.me/qunthuul",
                    description="FadhlanBot Main Menu",
                    thumb_url="https://i.ibb.co/2SMX7vV/20211010-112307.jpg",
                    reply_markup=InlineKeyboardMarkup(main_menu_buttons())
                )
            )
            if '-' in inline_query.query:
                _id, msg = inline_query.query.split('-', maxsplit=1)
                if not msg:
                    return
                if not msg.strip().endswith(':'):
                    return
                try:
                    user = await userge.get_users(_id.strip())
                except Exception:  # pylint: disable=broad-except
                    return
                PRVT_MSGS[inline_query.id] = (user.id, user.first_name, msg.strip(': '))
                prvte_msg = [[InlineKeyboardButton(
                    "Show Message 🔐", callback_data=f"prvtmsg({inline_query.id})")]]
                msg_c = f"🔒 A **private message** to {'@' + user.username}, "
                msg_c += "Only he/she can open it."
                results.append(
                    InlineQueryResultArticle(
                        id=uuid4(),
                        title=f"A Private Msg to {user.first_name}",
                        input_message_content=InputTextMessageContent(msg_c),
                        description="Only he/she can open it",
                        thumb_url="https://i.ibb.co/2SMX7vV/20211010-112307.jpg",
                        reply_markup=InlineKeyboardMarkup(prvte_msg)
                    )
                )
            elif "pmpermit" in inline_query.query:
                owner = await userge.get_me()
                pm_inline_msg = await SAVED_SETTINGS.find_one({'_id': 'CUSTOM_INLINE_PM_MESSAGE'})
                if pm_inline_msg:
                    text = pm_inline_msg.get('data')
                else:
                    text = f"Hello, welcome to **{owner.first_name}** Dm.\n\nWhat you want to do ?"
                buttons = [[
                    InlineKeyboardButton(
                        "Contact Me", callback_data="pm_contact"),
                    InlineKeyboardButton(
                        "Spam here", callback_data="pm_spam")]]
                results.append(
                    InlineQueryResultArticle(
                        id=uuid4(),
                        title="Pm Permit",
                        input_message_content=InputTextMessageContent(text),
                        description="Inline Pm Permit Handler",
                        thumb_url="https://i.ibb.co/2SMX7vV/20211010-112307.jpg",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                )
            elif "msg.err" in inline_query.query:
                if ' ' not in inline_query.query:
                    return
                tmp = inline_query.query.split(' ', maxsplit=2)
                if len(tmp) != 3:
                    return
                _, cmd, err_text = tmp
                if cmd and err_text and is_command(cmd):
                    bot_username = (await userge.bot.get_me()).username
                    button = [
                        [
                            InlineKeyboardButton(
                                "Info!", url=f"t.me/{bot_username}?start={cmd}"
                            )
                        ]
                    ]
                    results.append(
                        InlineQueryResultArticle(
                            id=uuid4(),
                            title="Inline Error Text",
                            input_message_content=InputTextMessageContent(err_text),
                            description="Inline Error text with help support button.",
                            thumb_url="https://i.ibb.co/2SMX7vV/20211010-112307.jpg",
                            reply_markup=InlineKeyboardMarkup(button)
                        )
                    )

        await inline_query.answer(results=results, cache_time=3)
