// modules/owner/broadcast.js
// In production, you’d maintain a list of all user/chat IDs.
const subscribers = new Set();
module.exports = (bot) => {
  // Subscribe users on /start (for demo purposes)
  bot.use((ctx, next) => {
    if (ctx.from && ctx.chat && ctx.chat.type === 'private') {
      subscribers.add(ctx.from.id);
    }
    return next();
  });

  bot.command('broadcast', (ctx) => {
    // Only allow the bot owner (replace OWNER_ID with your ID)
    if (ctx.from.id !== Number(process.env.OWNER_ID)) {
      return ctx.reply('Unauthorized.');
    }
    const message = ctx.message.text.split(' ').slice(1).join(' ');
    subscribers.forEach(userId => {
      bot.telegram.sendMessage(userId, `[Broadcast]: ${message}`).catch(() => {});
    });
    ctx.reply('Broadcast sent.');
  });
};
