exports.init = (bot) => {
  bot.command('id', (ctx) => {
    let response = `Your ID: ${ctx.from.id}\n`;
    if (ctx.chat) response += `Chat ID: ${ctx.chat.id}`;
    ctx.reply(response);
  });
};

exports.help = [
  { name: '/id', description: 'Get your ID and chat ID.', category: 'INFO' }
];
