exports.init = (bot) => {
  bot.command('deletecmd', (ctx) => {
    ctx.deleteMessage().catch((error) => {
      console.error('Deletecmd error:', error);
      ctx.reply('Unable to delete command message.');
    });
  });
};

exports.help = [
  { name: '/deletecmd', description: 'Delete the command message.', category: 'CHAT' }
];
