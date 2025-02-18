exports.init = (bot) => {
  bot.command('adminlist', async (ctx) => {
    try {
      const admins = await ctx.telegram.getChatAdministrators(ctx.chat.id);
      const list = admins.map(a => a.user.username ? '@' + a.user.username : a.user.first_name).join(', ');
      ctx.reply(`Admins: ${list}`);
    } catch (error) {
      console.error('Adminlist error:', error);
      ctx.reply('Failed to fetch admin list.');
    }
  });
};

exports.help = [
  { name: '/adminlist', description: 'List all administrators in the chat.', category: 'ADMIN' }
];
