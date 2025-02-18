exports.init = (bot) => {
  bot.command('report', (ctx) => {
    try {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Please reply to the message you want to report.');
      ctx.reply(`User ${reply.from.id} has been reported. Admins have been notified.`);
      if (ctx.sendLog) {
        ctx.sendLog(`[LOG] User reported by @${ctx.from.username} in ${ctx.chat.title}. Reported user: ${reply.from.id}`).catch(err => console.error(err));
      }
    } catch (error) {
      console.error('Report error:', error);
      ctx.reply('Failed to report.');
    }
  });
};

exports.help = [
  { name: '/report', description: 'Report a user/message for admin intervention.', category: 'ADMIN' }
];
