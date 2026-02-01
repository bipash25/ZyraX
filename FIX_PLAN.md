# Issues and Fix Plan

## Critical Issues Identified

1.  **Command Arguments vs. Replies**: `/ban`, `/mute`, `/promote`, etc., strictly enforce `reply_to_message`. They ignore arguments like `@user` or User IDs.
    *   **Fix**: Update `extract_user` logic in all admin commands to check `message.command[1]` if no reply is present.

2.  **Admin List Empty**: `/adminlist` returns nothing.
    *   **Fix**: Debug `client.get_chat_members(filter="administrators")`. It might be an async generator issue or Pyrogram version quirk.

3.  **Blacklist Logic Flaws**:
    *   **Self-Triggering**: Setting a blacklist word triggers the blacklist on the setting command itself.
    *   **Admin Immunity Failure**: Admins are being warned/deleted despite the check.
    *   **Fix**:
        *   Ignore messages starting with `/` in blacklist watcher.
        *   Fix the admin check logic (ensure we are awaiting `get_member` correctly and checking status properly).

4.  **Notes (`/get`) Broken**: `/get mf` failed silently or returned usage error.
    *   **Fix**: Verify `get_note` logic. The usage error suggests `len(message.command) < 2` but the user provided an arg. Might be a parsing issue.

5.  **Reports Error**: `/report` returned "Something went wrong".
    *   **Fix**: Likely an issue iterating `get_chat_members` or sending the report. Debug logging needed.

6.  **Welcome Message Missing**: Only Captcha triggers.
    *   **Fix**: The `welcome` and `captcha_handler` both listen to `new_chat_members`. One might be stopping propagation or they are racing. Ensure `group=` parameter is set correctly so both run.

7.  **Captcha Issues**:
    *   **Race Condition**: Sent before user can see history? (Telegram issue, but we can delay slightly).
    *   **Timeout**: User asked if timeout exists. We implemented `asyncio.sleep(60)` task in Phase 2, but maybe it's not working or user didn't see it kick.

8.  **Promote Error**: `unexpected keyword argument 'can_change_info'`.
    *   **Fix**: Pyrogram `promote_chat_member` arguments have changed or I am using the wrong names. Check Pyrogram docs/source (it uses `privileges=ChatPrivileges(...)` object now in v2.0+).

9.  **Sysinfo/GPU**: Missing commands/tools.
    *   **Fix**: Just informational, but we can make them fail gracefully or hide them if not owner.

## Plan for Phase 3 Fixes + Phase 4

1.  **Fix Core Admin Commands**: Update `bans.py`, `admin.py`, `warnings.py` to accept arguments.
2.  **Fix Promote**: Update to use `ChatPrivileges`.
3.  **Fix Blacklist**: Ignore commands, fix admin check.
4.  **Fix Welcome/Captcha**: Adjust handler groups. Add slight delay to captcha.
5.  **Fix Reports**: Debug and fix.
6.  **Deploy Phase 3**: Apply the Notes/Filters/Karma upgrades which might fix the `/get` issue (as Phase 3 rewrote Notes).
7.  **Start Phase 4**: Games & Economy.

I will start by fixing the **Promote** and **Command Arguments** issues, then **Blacklist**, then **Welcome/Captcha**.
