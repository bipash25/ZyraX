exports.init = (bot) => {
  bot.command('rps', (ctx) => {
    const choices = ['rock', 'paper', 'scissors'];
    const args = ctx.message.text.split(' ').slice(1);
    if (!args[0] || !choices.includes(args[0].toLowerCase())) {
      return ctx.reply('Usage: /rps <rock|paper|scissors>');
    }
    const userChoice = args[0].toLowerCase();
    const botChoice = choices[Math.floor(Math.random() * choices.length)];
    let result = '';
    if (userChoice === botChoice) result = "It's a tie!";
    else if (
      (userChoice === 'rock' && botChoice === 'scissors') ||
      (userChoice === 'paper' && botChoice === 'rock') ||
      (userChoice === 'scissors' && botChoice === 'paper')
    ) result = 'You win!';
    else result = 'You lose!';
    ctx.reply(`You chose ${userChoice}, I chose ${botChoice}. ${result}`);
  });
};

exports.help = [
  { name: '/rps', description: 'Play Rock-Paper-Scissors. Usage: /rps <rock|paper|scissors>', category: 'FUN' }
];
