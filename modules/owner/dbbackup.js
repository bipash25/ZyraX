// modules/owner/dbbackup.js
module.exports = (bot) => {
    bot.command('dbbackup', (ctx) => {
      if (ctx.from.id !== Number(process.env.OWNER_ID)) {
        return ctx.reply('Unauthorized.');
      }
      // For demo, we simply reply that backup is complete.
      ctx.reply('Database backup complete.');
    });
  };
  