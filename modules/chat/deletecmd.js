// modules/chat/deletecmd.js
module.exports = (bot) => {
    bot.command('deletecmd', (ctx) => {
      // Simply delete the triggering message.
      ctx.deleteMessage().catch(() => ctx.reply('Unable to delete command message.'));
    });
  };
  