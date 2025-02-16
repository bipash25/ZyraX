// modules/admin/kick.js
module.exports = (bot) => {
    bot.command('kick', async (ctx) => {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Please reply to the user to kick.');
      const targetId = reply.from.id;
      try {
        // Kick by unbanning immediately.
        await ctx.telegram.unbanChatMember(ctx.chat.id, targetId);
        ctx.reply(`User ${targetId} has been kicked.`);
      } catch (error) {
        ctx.reply('Failed to kick the user. Check permissions.');
      }
    });
  };
  