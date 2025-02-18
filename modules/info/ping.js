exports.init = (bot) => {
  bot.command('ping', async (ctx) => {
    try {
      const start = Date.now();
      await ctx.reply('Pinging...');
      const latency = Date.now() - start;
      ctx.reply(`Pong! Latency is ${latency}ms.`);
    } catch (error) {
      console.error('Ping error:', error);
    }
  });
};

exports.help = [
  { name: '/ping', description: 'Check bot latency.', category: 'INFO' }
];
