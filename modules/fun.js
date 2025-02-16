module.exports = (bot) => {
  // /roll command: returns a random number between 1 and 6
  bot.command('roll', (ctx) => {
    const result = Math.floor(Math.random() * 6) + 1;
    ctx.reply(`You rolled a ${result}!`);
  });

  // /coinflip command: returns Heads or Tails
  bot.command('coinflip', (ctx) => {
    const result = Math.random() < 0.5 ? 'Heads' : 'Tails';
    ctx.reply(`Coinflip: ${result}!`);
  });

  // /8ball command: returns a random response
  bot.command('8ball', (ctx) => {
    const responses = [
      'It is certain.',
      'Reply hazy, try again.',
      'Don’t count on it.',
      'Absolutely!',
      'My sources say no.',
      'Outlook not so good.'
    ];
    const answer = responses[Math.floor(Math.random() * responses.length)];
    ctx.reply(answer);
  });
};