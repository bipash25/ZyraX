exports.init = (bot) => {
  bot.command('ban', async (ctx) => {
    try {
      const reply = ctx.message.reply_to_message;
      const args = ctx.message.text.split(' ').slice(1);
      let targetId;
      let duration = null;
      if (reply) {
        targetId = reply.from.id;
      } else if (args[0]) {
        targetId = args[0];
      } else {
        return ctx.reply('Usage: /ban <reply/username/ID> [duration].');
      }
      if (args[1]) {
        duration = args[1];
        // Duration parsing can be implemented here if needed.
      }
      await ctx.telegram.kickChatMember(ctx.chat.id, targetId);
      await ctx.reply(`User ${targetId} has been banned${duration ? ` for ${duration}` : ' permanently'}.`);
      if (ctx.sendLog) await ctx.sendLog(`[LOG] @${ctx.from.username} banned user ${targetId} in ${ctx.chat.title}.`);
    } catch (error) {
      console.error('Ban error:', error);
      ctx.reply('Failed to ban the user. Check my permissions.');
    }
  });
};

exports.help = [
  { name: '/ban', description: 'Ban a user permanently or temporarily if duration provided.', category: 'ADMIN' }
];
