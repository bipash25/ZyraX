exports.init = (bot) => {
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

exports.help = [
  { name: '/8ball', description: 'Ask the magic 8-ball a question.', category: 'FUN' }
];
