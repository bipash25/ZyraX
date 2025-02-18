const words = ['telegram', 'bot', 'javascript', 'zyrax'];
function scramble(word) {
  return word.split('').sort(() => Math.random() - 0.5).join('');
}

exports.init = (bot) => {
  bot.command('guessword', (ctx) => {
    const word = words[Math.floor(Math.random() * words.length)];
    const scrambled = scramble(word);
    ctx.session = ctx.session || {};
    ctx.session.guessword = { word };
    ctx.reply(`Unscramble this word: ${scrambled}`);
  });

  bot.on('text', async (ctx, next) => {
    if (ctx.session && ctx.session.guessword) {
      const correct = ctx.session.guessword.word;
      if (ctx.message.text.trim().toLowerCase() === correct.toLowerCase()) {
        await ctx.reply('🎉 Correct!');
      } else {
        await ctx.reply(`❌ Wrong. The correct word is "${correct}".`);
      }
      ctx.session.guessword = null;
    } else {
      return next();
    }
  });
};

exports.help = [
  { name: '/guessword', description: 'Play the word unscramble game.', category: 'FUN' }
];
