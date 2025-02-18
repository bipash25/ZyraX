const floodCounters = {}; // floodCounters[chatId][userId] = { count, lastTimestamp }
const DEFAULT_LIMIT = 5;
exports.init = (bot) => {
  bot.use(async (ctx, next) => {
    if (ctx.chat && ctx.from && ctx.message && ctx.message.text) {
      const chatId = ctx.chat.id;
      const userId = ctx.from.id;
      if (!floodCounters[chatId]) floodCounters[chatId] = {};
      const userData = floodCounters[chatId][userId] || { count: 0, lastTimestamp: Date.now() };
      const now = Date.now();
      if (now - userData.lastTimestamp > 5000) {
        userData.count = 0;
      }
      userData.count++;
      userData.lastTimestamp = now;
      floodCounters[chatId][userId] = userData;
      if (userData.count > DEFAULT_LIMIT) {
        try {
          await ctx.telegram.restrictChatMember(ctx.chat.id, userId, {
            permissions: { can_send_messages: false },
            until_date: Math.floor(Date.now() / 1000) + 30
          });
          await ctx.reply(`@${ctx.from.username || ctx.from.first_name} is flooding and has been muted for 30 seconds.`);
        } catch (e) {
          console.error('Antiflood mute error:', e);
        }
      }
    }
    return next();
  });
  
  bot.command('setantiflood', (ctx) => {
    try {
      const args = ctx.message.text.split(' ').slice(1);
      if (!args[0]) return ctx.reply(`Default antiflood limit is ${DEFAULT_LIMIT} messages.`);
      ctx.reply(`Antiflood limit set to ${args[0]} messages (demo only).`);
    } catch (error) {
      console.error('SetAntiflood error:', error);
      ctx.reply('Error setting antiflood.');
    }
  });
};

exports.help = [
  { name: '/setantiflood', description: 'Configure antiflood settings (demo only).', category: 'ADMIN' }
];
