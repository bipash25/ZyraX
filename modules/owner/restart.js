exports.init = (bot) => {
  bot.command('restart', (ctx) => {
    if (ctx.from.id !== Number(process.env.OWNER_ID)) return ctx.reply('Unauthorized.');
    ctx.reply('Restarting...').then(() => process.exit(0));
  });
};

exports.help = [
  { name: '/restart', description: 'Restart the bot (Owner only).', category: 'OWNER' }
];
