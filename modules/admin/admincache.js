// modules/admin/admincache.js
module.exports = (bot) => {
    bot.command('admincache', async (ctx) => {
      try {
        await ctx.telegram.getChatAdministrators(ctx.chat.id);
        ctx.reply('Admin cache refreshed.');
      } catch (error) {
        ctx.reply('Failed to refresh admin cache.');
      }
    });
  };
  