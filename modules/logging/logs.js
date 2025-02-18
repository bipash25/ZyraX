exports.init = (bot) => {
  bot.command('logs', (ctx) => {
    ctx.reply('Displaying logs is not implemented yet.');
  });
};

exports.help = [
  { name: '/logs', description: 'Display recent logs of chat activity.', category: 'LOGGING' }
];
