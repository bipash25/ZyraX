// modules/admin/antiraid.js
const joinCounts = {}; // chatId -> { count, startTime }
const RAID_THRESHOLD = 15; // e.g., 15 joins per minute triggers antiraid.
const RAID_BAN_DURATION = 3600; // seconds (1 hour)

module.exports = (bot) => {
  bot.on('new_chat_members', async (ctx) => {
    const chatId = ctx.chat.id;
    const now = Date.now();
    if (!joinCounts[chatId]) joinCounts[chatId] = { count: 0, startTime: now };
    const data = joinCounts[chatId];
    if (now - data.startTime > 60000) {
      data.count = 1;
      data.startTime = now;
    } else {
      data.count++;
      if (data.count > RAID_THRESHOLD) {
        // Temporarily ban the new user.
        const newUserId = ctx.message.new_chat_members[0].id;
        try {
          await ctx.telegram.kickChatMember(chatId, newUserId, {
            until_date: Math.floor(Date.now() / 1000) + RAID_BAN_DURATION
          });
          ctx.reply(`Antiraid: User ${newUserId} temporarily banned.`);
        } catch (e) {
          // Ignore errors.
        }
      }
    }
  });
};
