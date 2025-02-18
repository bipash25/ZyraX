const autoReplies = {}; // autoReplies[chatId] = { trigger: reply }
exports.init = (bot) => {
  bot.command('autoreply', (ctx) => {
    try {
      const parts = ctx.message.text.split(' ');
      if (parts.length < 3) return ctx.reply('Usage: /autoreply <trigger> <reply>');
      const trigger = parts[1].toLowerCase();
      const replyMsg = parts.slice(2).join(' ');
      const chatId = ctx.chat.id;
      if (!autoReplies[chatId]) autoReplies[chatId] = {};
      autoReplies[chatId][trigger] = replyMsg;
      ctx.reply(`Auto-reply set: When someone says "${trigger}", reply with "${replyMsg}".`);
    } catch (error) {
      console.error('Autoreply error:', error);
      ctx.reply('Error setting auto-reply.');
    }
  });

  bot.on('text', (ctx, next) => {
    try {
      const chatId = ctx.chat.id;
      if (autoReplies[chatId]) {
        const msg = ctx.message.text.toLowerCase();
        for (let trigger in autoReplies[chatId]) {
          if (msg.includes(trigger)) {
            return ctx.reply(autoReplies[chatId][trigger]);
          }
        }
      }
    } catch (error) {
      console.error('Autoreply handler error:', error);
    }
    return next();
  });
};

exports.help = [
  { name: '/autoreply', description: 'Set an auto-reply trigger and response.', category: 'CHAT' }
];
