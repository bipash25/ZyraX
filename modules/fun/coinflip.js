exports.init = (bot) => {
  bot.command('coinflip', (ctx) => {
    const result = Math.random() < 0.5 ? 'Heads' : 'Tails';
    ctx.reply(`🪙 Coinflip result: ${result}`);
  });
};

exports.help = [
  { name: '/coinflip', description: 'Flip a coin.', category: 'FUN' }
];
