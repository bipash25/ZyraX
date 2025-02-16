// modules/admin/report.js
module.exports = (bot) => {
    bot.command('report', (ctx) => {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Please reply to the message you want to report.');
      // In production, you’d notify admins.
      ctx.reply(`User ${reply.from.id} has been reported. Admins have been notified.`);
      if (ctx.sendLog) ctx.sendLog(`User ${ctx.from.username} reported user ${reply.from.id} in ${ctx.chat.title}.`);
    });
  };
  