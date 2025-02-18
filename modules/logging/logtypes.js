exports.init = (bot) => {
  bot.command('logtypes', (ctx) => {
    const types = ['bans', 'joins', 'messages', 'admin actions'];
    ctx.reply(`Supported log types: ${types.join(', ')}`);
  });
};

exports.help = [
  { name: '/logtypes', description: 'List supported log categories.', category: 'LOGGING' }
];
