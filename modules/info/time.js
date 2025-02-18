exports.init = (bot) => {
  bot.command('time', (ctx) => {
    const now = new Date();
    ctx.reply(`Current server time: ${now.toLocaleString()}`);
  });
};

exports.help = [
  { name: '/time', description: 'Get current server time.', category: 'INFO' }
];
