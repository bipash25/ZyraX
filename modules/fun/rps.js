// modules/fun/rps.js
module.exports = (bot) => {
    bot.command('rps', (ctx) => {
      const choices = ['rock', 'paper', 'scissors'];
      const userChoice = ctx.message.text.split(' ')[1];
      if (!userChoice || !choices.includes(userChoice.toLowerCase())) {
        return ctx.reply('Usage: /rps <rock|paper|scissors>');
      }
      const botChoice = choices[Math.floor(Math.random() * choices.length)];
      let result = '';
      if (userChoice === botChoice) result = 'It\'s a tie!';
      else if (
        (userChoice === 'rock' && botChoice === 'scissors') ||
        (userChoice === 'paper' && botChoice === 'rock') ||
        (userChoice === 'scissors' && botChoice === 'paper')
      ) result = 'You win!';
      else result = 'You lose!';
      ctx.reply(`You chose ${userChoice}, I chose ${botChoice}. ${result}`);
    });
  };
  