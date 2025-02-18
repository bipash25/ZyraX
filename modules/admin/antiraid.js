const joinCounts = {}; // joinCounts[chatId] = { count, startTime }
const RAID_THRESHOLD = 15; // joins per minute
const RAID_BAN_DURATION = 3600; // seconds (1 hour)
exports.init = (bot) => {
  bot.on('new_chat_members', async (ctx) => {
    try {
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
          const newUserId = ctx.message.new_chat_members[0].id;
          try {
            await ctx.telegram.kickChatMember(chatId, newUserId, {
              until_date: Math.floor(Date.now() / 1000) + RAID_BAN_DURATION
            });
            await ctx.reply(`Antiraid activated: User ${newUserId} temporarily banned for 1 hour.`);
          } catch (err) {
            console.error('Antiraid ban error:', err);
          }
        }
      }
    } catch (error) {
      console.error('Antiraid error:', error);
    }
  });
  
  bot.command('antiraid', (ctx) => {
    try {
      const arg = ctx.message.text.split(' ')[1];
      if (!arg || arg.toLowerCase() === 'on') {
        ctx.reply('Antiraid enabled.');
      } else if (arg.toLowerCase() === 'off') {
        ctx.reply('Antiraid disabled.');
      } else {
        ctx.reply('Usage: /antiraid <on/off>');
      }
    } catch (error) {
      console.error('Antiraid command error:', error);
      ctx.reply('Error toggling antiraid.');
    }
  });
};

exports.help = [
  { name: '/antiraid', description: 'Toggle antiraid to temporarily ban mass joiners.', category: 'ADMIN' }
];
