// modules/fun/8ball.js
module.exports = (bot) => {
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
      ctx.reply(`🎱 ${answer}`);
    });
  };
  