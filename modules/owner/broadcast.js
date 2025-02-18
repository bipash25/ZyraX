const subscribers = new Set();
exports.init = (bot) => {
  // Subscribe users in private chats.
  bot.use((ctx, next) => {
    if (ctx.chat && ctx.chat.type === 'private' && ctx.from) {
      subscribers.add(ctx.from.id);
    }
    return next();
  });
  
  bot.command('broadcast', async (ctx) => {
    try {
      if (ctx.from.id !== Number(process.env.OWNER_ID)) return ctx.reply('Unauthorized.');
      const message = ctx.message.text.split(' ').slice(1).join(' ');
      if (!message) return ctx.reply('Usage: /broadcast <message>');
      subscribers.forEach(userId => {
        bot.telegram.sendMessage(userId, `[Broadcast]: ${message}`).catch(() => {});
      });
      ctx.reply('Broadcast sent.');
    } catch (error) {
      console.error('Broadcast error:', error);
      ctx.reply('Broadcast failed.');
    }
  });
};

exports.help = [
  { name: '/broadcast', description: 'Send a message to all subscribed users (Owner only).', category: 'OWNER' }
];
