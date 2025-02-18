const adminErrorEnabled = {}; // adminErrorEnabled[chatId] = boolean
exports.init = (bot) => {
  bot.command('adminerror', (ctx) => {
    try {
      const chatId = ctx.chat.id;
      const arg = ctx.message.text.split(' ')[1];
      if (!arg) return ctx.reply('Usage: /adminerror <on/off>');
      adminErrorEnabled[chatId] = arg.toLowerCase() === 'on';
      ctx.reply(`Admin error messages ${adminErrorEnabled[chatId] ? 'enabled' : 'disabled'}.`);
    } catch (error) {
      console.error('Adminerror error:', error);
      ctx.reply('Error toggling admin error messages.');
    }
  });
};

exports.help = [
  { name: '/adminerror', description: 'Toggle admin error messages.', category: 'ADMIN' }
];
