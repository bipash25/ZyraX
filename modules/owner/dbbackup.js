exports.init = (bot) => {
  bot.command('dbbackup', (ctx) => {
    if (ctx.from.id !== Number(process.env.OWNER_ID)) return ctx.reply('Unauthorized.');
    // In a real implementation, perform database backup here.
    ctx.reply('Database backup complete.');
  });
};

exports.help = [
  { name: '/dbbackup', description: 'Backup the bot’s database (Owner only).', category: 'OWNER' }
];

  