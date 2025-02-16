// modules/info/time.js
module.exports = (bot) => {
    bot.command('time', (ctx) => {
      const now = new Date();
      ctx.reply(`Current server time: ${now.toLocaleString()}`);
    });
  };
  