const warnLimits = {}; // warnLimits[chatId] = number
exports.init = (bot) => {
  bot.command('warnlimit', (ctx) => {
    try {
      const args = ctx.message.text.split(' ').slice(1);
      const chatId = ctx.chat.id;
      if (args.length === 0) {
        const current = warnLimits[chatId] || 3;
        return ctx.reply(`Current warning limit is ${current}.`);
      }
      const newLimit = parseInt(args[0]);
      if (isNaN(newLimit)) return ctx.reply('Please provide a valid number.');
      warnLimits[chatId] = newLimit;
      ctx.reply(`Warning limit set to ${newLimit}.`);
    } catch (error) {
      console.error('Warnlimit error:', error);
      ctx.reply('Failed to set warning limit.');
    }
  });
};

exports.help = [
  { name: '/warnlimit', description: 'Set or check the warning limit for auto actions.', category: 'ADMIN' }
];
