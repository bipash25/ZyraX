exports.init = (bot) => {
  bot.command('eval', (ctx) => {
    if (ctx.from.id !== Number(process.env.OWNER_ID)) return ctx.reply('Unauthorized.');
    try {
      const code = ctx.message.text.split(' ').slice(1).join(' ');
      const result = eval(code);
      ctx.reply(`Result: ${result}`);
    } catch (e) {
      ctx.reply(`Error: ${e.message}`);
    }
  });
};

exports.help = [
  { name: '/eval', description: 'Evaluate JavaScript code (Owner only).', category: 'OWNER' }
];
