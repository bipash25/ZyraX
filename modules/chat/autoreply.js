// modules/chat/autoreply.js
const autoReplies = {}; // chatId -> { trigger: reply }
module.exports = (bot) => {
  bot.command('autoreply', (ctx) => {
    const parts = ctx.message.text.split(' ');
    if (parts.length < 3) return ctx.reply('Usage: /autoreply <trigger> <reply>');
    const trigger = parts[1].toLowerCase();
    const replyMsg = parts.slice(2).join(' ');
    const chatId = ctx.chat.id;
    if (!autoReplies[chatId]) autoReplies[chatId] = {};
    autoReplies[chatId][trigger] = replyMsg;
    ctx.reply(`Auto-reply set: When someone says "${trigger}", reply with "${replyMsg}".`);
  });

  bot.on('text', (ctx, next) => {
    const chatId = ctx.chat.id;
    if (autoReplies[chatId]) {
      const msg = ctx.message.text.toLowerCase();
      for (let trigger in autoReplies[chatId]) {
        if (msg.includes(trigger)) {
          return ctx.reply(autoReplies[chatId][trigger]);
        }
      }
    }
    return next();
  });
};
