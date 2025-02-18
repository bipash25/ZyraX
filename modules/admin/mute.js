exports.init = (bot) => {
  bot.command('mute', async (ctx) => {
    try {
      const reply = ctx.message.reply_to_message;
      const args = ctx.message.text.split(' ').slice(1);
      if (!reply) return ctx.reply('Please reply to the user you want to mute.');
      const targetId = reply.from.id;
      const durationSec = parseInt(args[0]) || 60;
      await ctx.telegram.restrictChatMember(ctx.chat.id, targetId, {
        permissions: { can_send_messages: false },
        until_date: Math.floor(Date.now() / 1000) + durationSec
      });
      await ctx.reply(`User ${targetId} muted for ${durationSec} seconds.`);
    } catch (error) {
      console.error('Mute error:', error);
      ctx.reply('Failed to mute the user. Check my rights.');
    }
  });
};

exports.help = [
  { name: '/mute', description: 'Mute a user for a specified time (in seconds).', category: 'ADMIN' }
];
