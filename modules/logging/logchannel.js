const config = require('../../config');
exports.init = (bot) => {
  bot.command('logchannel', (ctx) => {
    ctx.reply(`Current log channel ID: ${config.LOG_CHANNEL_ID}`);
  });

  bot.command('setlog', (ctx) => {
    if (ctx.chat.type !== 'channel') return ctx.reply('Please send this command in the channel you wish to use as log channel.');
    config.LOG_CHANNEL_ID = ctx.chat.id;
    ctx.reply(`Log channel set to ${ctx.chat.id}`);
  });

  bot.command('unsetlog', (ctx) => {
    config.LOG_CHANNEL_ID = '';
    ctx.reply('Log channel has been unset.');
  });
};

exports.help = [
  { name: '/logchannel', description: 'Get or set the log channel.', category: 'LOGGING' }
];
