// modules/logging/logtypes.js
module.exports = (bot) => {
    bot.command('logtypes', (ctx) => {
      const types = ['bans', 'joins', 'messages', 'admin actions'];
      ctx.reply(`Supported log types: ${types.join(', ')}`);
    });
  };
  