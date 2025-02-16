// modules/fun/roll.js
module.exports = (bot) => {
    bot.command('roll', (ctx) => {
      const result = Math.floor(Math.random() * 6) + 1;
      ctx.reply(`🎲 You rolled a ${result}!`);
    });
  };
  