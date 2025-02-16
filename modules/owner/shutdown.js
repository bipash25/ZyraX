// modules/owner/shutdown.js
module.exports = (bot) => {
    bot.command('shutdown', (ctx) => {
      if (ctx.from.id !== Number(process.env.OWNER_ID)) {
        return ctx.reply('Unauthorized.');
      }
      ctx.reply('Shutting down...').then(() => process.exit(0));
    });
  };
  