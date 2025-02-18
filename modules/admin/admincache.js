exports.init = (bot) => {
  bot.command('admincache', async (ctx) => {
    try {
      await ctx.telegram.getChatAdministrators(ctx.chat.id);
      ctx.reply('Admin cache refreshed.');
    } catch (error) {
      console.error('Admincache error:', error);
      ctx.reply('Failed to refresh admin cache.');
    }
  });
};

exports.help = [
  { name: '/admincache', description: 'Refresh the admin cache immediately.', category: 'ADMIN' }
];
