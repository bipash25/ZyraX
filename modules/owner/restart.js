// modules/owner/restart.js
module.exports = (bot) => {
    bot.command('restart', (ctx) => {
      if (ctx.from.id !== Number(process.env.OWNER_ID)) {
        return ctx.reply('Unauthorized.');
      }
      ctx.reply('Restarting...').then(() => process.exit(0));
    });
  };
  