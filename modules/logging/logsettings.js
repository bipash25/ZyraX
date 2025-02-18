let logSettings = {}; // logSettings[chatId] = settings object
exports.init = (bot) => {
  bot.command('logsettings', (ctx) => {
    try {
      const chatId = ctx.chat.id;
      const args = ctx.message.text.split(' ').slice(1);
      if (args.length === 0) {
        return ctx.reply(`Current log settings: ${JSON.stringify(logSettings[chatId] || {})}`);
      }
      logSettings[chatId] = logSettings[chatId] || {};
      args.forEach(arg => {
        const [key, value] = arg.split('=');
        logSettings[chatId][key] = value;
      });
      ctx.reply(`Log settings updated: ${JSON.stringify(logSettings[chatId])}`);
    } catch (error) {
      console.error('Logsettings error:', error);
      ctx.reply('Error updating log settings.');
    }
  });
};

exports.help = [
  { name: '/logsettings', description: 'Configure which events should be logged.', category: 'LOGGING' }
];

