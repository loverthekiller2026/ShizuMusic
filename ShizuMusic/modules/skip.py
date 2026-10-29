# ═══════════════════════════════════════════════════════════════
#                     🎵 SHIZUMUSIC
#
#                   © 2026 BAD MUNDA
#
#                Developed with ❤️ by Bad Munda
#
#             Do not remove or alter the original credits.
#
#           Copyright © 2026 Bad Munda. All rights reserved.
#
#              
# ═══════════════════════════════════════════════════════════════

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.core.channels import target_chat
from ShizuMusic.core.player import get_active_panel, play_song
from ShizuMusic.core.queue import peek_current, pop_current, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.permissions import is_user_authorized
from richgram import rich_heading, rich_note, rich_send


@bot.on_message(
    filters.group
    & filters.command(["skip", "cskip"])
    & group_allowed
    & user_allowed
)
async def skip_cmd(_, message: Message) -> None:

    chat_id = await target_chat(message)
    if chat_id is None:
        return
    lang = chat_strings(chat_id)

    if not await is_user_authorized(message):
        await rich_send(
            bot, chat_id,
            rich_heading(lang["admin_only_title"], level=3)
            + rich_note(lang["admin_only_note"]),
        )
        return

    if not queue_size(chat_id):
        await rich_send(
            bot, chat_id,
            rich_heading(lang["queue_empty_title"], level=3)
            + rich_note(lang["skip_empty_note"]),
        )
        return

    # Remove the current queue entry immediately, then hand off to the next.
    skipped = pop_current(chat_id)
    if not skipped:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["queue_empty_title"], level=3)
            + rich_note(lang["skip_empty_note"]),
        )
        return

    try:
        delete_file(skipped.get("file_path", ""))
    except Exception:
        pass

    nxt = peek_current(chat_id)
    if not nxt:
        try:
            from ShizuMusic.core.autoplay import autoplay_next
            if await autoplay_next(chat_id, skipped):
                nxt = peek_current(chat_id)
        except Exception:
            pass

    if nxt:
        try:
            from ShizuMusic.core.autoplay import schedule_prefetch
            schedule_prefetch(chat_id, nxt)
        except Exception:
            pass

        # Reuse the existing now-playing panel instead of creating two
        # transient messages for every skip.
        panel = get_active_panel(chat_id)
        if panel is None:
            panel = await rich_send(
                bot, chat_id,
                rich_heading(lang["skip_skipping_title"], level=3),
            )
        await play_song(chat_id, panel, nxt)
        return

    # No next song: stop the old stream as well as clearing the queue.
    from ShizuMusic.core.call import leave_vc
    await leave_vc(chat_id)
    await rich_send(
        bot, chat_id,
        rich_heading(lang["skip_skipped_title"], level=3)
        + rich_note(lang["skip_queue_empty_note"]),
    )
