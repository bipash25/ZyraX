// modules/info/stats.js
let commandCount = 0;
module.exports = (bot) => {
  // Increment command count for every command (example)
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
