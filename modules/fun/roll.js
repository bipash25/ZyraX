exports.init = (bot) => {
  bot.command('roll', (ctx) => {
    const result = Math.floor(Math.random() * 6) + 1;
    ctx.reply(`🎲 You rolled a ${result}!`);
  });
};

exports.help = [
  { name: '/roll', description: 'Roll a dice.', category: 'FUN' }
];
