// modules/admin/ban.js
module.exports = (bot) => {
  bot.command('ban', async (ctx) => {
    // Check if the message is a reply or contains a username/ID
    const reply = ctx.message.reply_to_message;
    let target;
    let duration = null;  // Optional duration for temporary bans

    // Parse arguments: e.g., /ban [userid or @username] [duration]
    const args = ctx.message.text.split(' ').slice(1);
    if (reply) {
      target = reply.from.id;
    } else if (args[0]) {
      target = args[0];  // This should be processed (user ID or username)
    } else {
      return ctx.reply('Usage: /ban <reply/username/ID> [duration]');
    }

    // Optional: Parse duration if provided (like "2h", "3d", etc.)
    if (args[1]) {
      duration = args[1];
      // Here, convert duration string to a Date or timestamp.
    }

    // Perform the ban (placeholder logic)
    try {
      // If duration is specified, schedule an unban after that time.
      await ctx.telegram.kickChatMember(ctx.chat.id, target);
      ctx.reply(`User ${target} has been banned${duration ? ` for ${duration}` : ' permanently'}.`);
      // Log this action if logging is enabled.
      if (ctx.sendLog) ctx.sendLog(`Ban: User ${target} banned by ${ctx.from.username} in ${ctx.chat.title}`);
    } catch (err) {
      ctx.reply('Failed to ban the user. Make sure I have the proper admin rights.');
    }
  });
};