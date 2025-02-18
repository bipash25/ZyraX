const warnings = {}; // warnings[chatId][userId] = count
exports.init = (bot) => {
  bot.command('warn', (ctx) => {
    try {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Please reply to the user you want to warn.');
      const chatId = ctx.chat.id;
      const userId = reply.from.id;
      if (!warnings[chatId]) warnings[chatId] = {};
      warnings[chatId][userId] = (warnings[chatId][userId] || 0) + 1;
      ctx.reply(`User ${userId} warned. Total warnings: ${warnings[chatId][userId]}.`);
      if (ctx.sendLog) {
        ctx.sendLog(`[LOG] @${ctx.from.username} warned user ${userId} in ${ctx.chat.title}. Total warnings: ${warnings[chatId][userId]}.`)
          .catch(err => console.error(err));
      }
    } catch (error) {
      console.error('Warn error:', error);
      ctx.reply('Failed to warn the user.');
    }
  });
};

exports.help = [
  { name: '/warn', description: 'Warn a user and track warnings in memory.', category: 'ADMIN' }
];
