// modules/info/ping.js
module.exports = (bot) => {
    bot.command('ping', (ctx) => {
      const start = Date.now();
      ctx.reply('Pinging...').then(() => {
        const latency = Date.now() - start;
        ctx.reply(`Pong! Latency is ${latency}ms.`);
      });
    });
  };
  