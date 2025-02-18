exports.init = (bot) => {
  bot.command('kick', async (ctx) => {
    try {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Please reply to the user you want to kick.');
      const targetId = reply.from.id;
      await ctx.telegram.unbanChatMember(ctx.chat.id, targetId);
      await ctx.reply(`User ${targetId} has been kicked.`);
    } catch (error) {
      console.error('Kick error:', error);
      ctx.reply('Failed to kick the user. Check my permissions.');
    }
  });
};

exports.help = [
  { name: '/kick', description: 'Kick a user (they can rejoin).', category: 'ADMIN' }
];
