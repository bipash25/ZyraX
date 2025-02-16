// modules/fun/guessword.js
const words = ['telegram', 'bot', 'javascript', 'zyrax'];
module.exports = (bot) => {
  bot.command('guessword', (ctx) => {
    const word = words[Math.floor(Math.random() * words.length)];
    const scrambled = word.split('').sort(() => Math.random() - 0.5).join('');
    ctx.reply(`Unscramble this word: ${scrambled}`);
    bot.once('text', (answerCtx) => {
      if (answerCtx.message.text.trim().toLowerCase() === word) {
        answerCtx.reply('Correct!');
      } else {
        answerCtx.reply(`Wrong. The correct word was "${word}".`);
      }
    });
  });
};
