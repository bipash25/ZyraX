const anonAdminEnabled = {}; // anonAdminEnabled[chatId] = boolean
exports.init = (bot) => {
  bot.command('anonadmin', (ctx) => {
    try {
      const chatId = ctx.chat.id;
      const arg = ctx.message.text.split(' ')[1];
      if (!arg) return ctx.reply('Usage: /anonadmin <on/off>');
      anonAdminEnabled[chatId] = arg.toLowerCase() === 'on';
      ctx.reply(`Anonymous admin usage ${anonAdminEnabled[chatId] ? 'enabled' : 'disabled'}.`);
    } catch (error) {
      console.error('Anonadmin error:', error);
      ctx.reply('Error toggling anonadmin.');
    }
  });
};

exports.help = [
  { name: '/anonadmin', description: 'Toggle anonymous admin usage.', category: 'ADMIN' }
];
