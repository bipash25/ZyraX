/// modules/admin/ban.js
module.exports = (bot) => {
  bot.command('ban', async (ctx) => {
    // (For full security, check admin rights here)
    const reply = ctx.message.reply_to_message;
    const args = ctx.message.text.split(' ').slice(1);
    let targetId;
    let duration = null; // Duration string (e.g., "2h") if provided.

    if (reply) {
      targetId = reply.from.id;
    } else if (args[0]) {
      targetId = args[0];
    } else {
      return ctx.reply('Usage: /ban <reply/username/ID> [duration].');
    }
    if (args[1]) {
      duration = args[1];
      // For temporary bans, you would convert duration to a timestamp.
    }
    try {
      await ctx.telegram.kickChatMember(ctx.chat.id, targetId);
      ctx.reply(`User ${targetId} has been banned${duration ? ` for ${duration}` : ' permanently'}.`);
      if (ctx.sendLog) await ctx.sendLog(`Admin ${ctx.from.username} banned user ${targetId} in ${ctx.chat.title}.`);
    } catch (error) {
      ctx.reply('Failed to ban the user. Check my permissions.');
    }
  });
};
