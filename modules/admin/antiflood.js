// modules/admin/antiflood.js
const floodCounters = {}; // chatId -> { userId: { count, lastTimestamp } }
const DEFAULT_LIMIT = 5;

module.exports = (bot) => {
  bot.use((ctx, next) => {
    if (ctx.chat && ctx.from) {
      const chatId = ctx.chat.id;
      const userId = ctx.from.id;
      if (!floodCounters[chatId]) floodCounters[chatId] = {};
      const userData = floodCounters[chatId][userId] || { count: 0, lastTimestamp: Date.now() };
      const now = Date.now();
      // Reset counter if more than 5 seconds since last message.
      if (now - userData.lastTimestamp > 5000) userData.count = 0;
      userData.count++;
      userData.lastTimestamp = now;
      floodCounters[chatId][userId] = userData;
      if (userData.count > DEFAULT_LIMIT) {
        // Take action: mute user for 30 seconds.
        ctx.telegram.restrictChatMember(ctx.chat.id, userId, {
          permissions: { can_send_messages: false },
          until_date: Math.floor(Date.now() / 1000) + 30
        }).catch(() => {});
        ctx.reply(`User ${ctx.from.username} is flooding and has been muted for 30 seconds.`);
      }
    }
    return next();
  });
  
  bot.command('setantiflood', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    if (!args[0]) return ctx.reply(`Current flood limit is ${DEFAULT_LIMIT} messages.`);
    // For simplicity, we only log the change.
    // In production, store this per chat.
    ctx.reply(`Antiflood limit changed to ${args[0]} messages (not really enforced in this demo).`);
  });
};
