// modules/fun/trivia.js
const triviaQuestions = [
    { q: 'What is the capital of France?', a: 'Paris' },
    { q: 'What is 2+2?', a: '4' }
  ];
  
  module.exports = (bot) => {
    bot.command('trivia', (ctx) => {
      const question = triviaQuestions[Math.floor(Math.random() * triviaQuestions.length)];
      ctx.reply(`Trivia: ${question.q}\nReply with your answer!`);
      // For simplicity, we wait for the next message as answer.
      bot.once('text', (answerCtx) => {
        if (answerCtx.message.text.trim().toLowerCase() === question.a.toLowerCase()) {
          answerCtx.reply('Correct!');
        } else {
          answerCtx.reply(`Wrong. The answer is ${question.a}.`);
        }
      });
    });
  };
  