let commandCount = 0;
exports.init = (bot) => {
  bot.use((ctx, next) => {
    if (ctx.message && ctx.message.text && ctx.message.text.startsWith('/')) {
      commandCount++;
    }
    return next();
  });
  
  bot.command('stats', (ctx) => {
    ctx.reply(`Total commands processed: ${commandCount}`);
  });
};

exports.help = [
  { name: '/stats', description: 'Show bot command statistics.', category: 'INFO' }
];
