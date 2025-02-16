// modules/info/admins.js
module.exports = (bot) => {
    bot.command('admins', async (ctx) => {
      try {
        const admins = await ctx.telegram.getChatAdministrators(ctx.chat.id);
        const list = admins.map(a => a.user.username || a.user.first_name).join(', ');
        ctx.reply(`Admins: ${list}`);
      } catch (error) {
        ctx.reply('Failed to fetch admin list.');
      }
    });
  };
  