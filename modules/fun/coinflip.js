// modules/fun/coinflip.js
module.exports = (bot) => {
    bot.command('coinflip', (ctx) => {
      const result = Math.random() < 0.5 ? 'Heads' : 'Tails';
      ctx.reply(`🪙 Coinflip result: ${result}`);
    });
  };
  