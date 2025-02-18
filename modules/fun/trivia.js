const triviaQuestions = [
  { q: 'What is the capital of France?', a: 'Paris' },
  { q: 'What is 2+2?', a: '4' },
  { q: 'Who wrote "Hamlet"?', a: 'Shakespeare' }
];

exports.init = (bot) => {
  bot.command('trivia', (ctx) => {
    const question = triviaQuestions[Math.floor(Math.random() * triviaQuestions.length)];
    ctx.session = ctx.session || {};
    ctx.session.trivia = question;
    ctx.reply(`Trivia: ${question.q}\nReply with your answer.`);
  });

  bot.on('text', async (ctx, next) => {
    if (ctx.session && ctx.session.trivia) {
      const correctAnswer = ctx.session.trivia.a;
      if (ctx.message.text.trim().toLowerCase() === correctAnswer.toLowerCase()) {
        await ctx.reply('🎉 Correct!');
      } else {
        await ctx.reply(`❌ Wrong. The answer is ${correctAnswer}.`);
      }
      ctx.session.trivia = null;
    } else {
      return next();
    }
  });
};

exports.help = [
  { name: '/trivia', description: 'Start a trivia game.', category: 'FUN' }
];
