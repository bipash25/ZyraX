exports.init = (bot) => {
  bot.command('update', (ctx) => {
    if (ctx.from.id !== Number(process.env.OWNER_ID)) return ctx.reply('Unauthorized.');
    // Simulate update – in a real bot, pull updates from repo etc.
    ctx.reply('Bot updated to the latest version.');
  });
};

exports.help = [
  { name: '/update', description: 'Update the bot (Owner only).', category: 'OWNER' }
];
