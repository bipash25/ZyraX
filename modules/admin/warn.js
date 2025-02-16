// modules/admin/warn.js
const warnings = {}; // Key: chatId, then userId -> count

module.exports = (bot) => {
  bot.command('warn', (ctx) => {
    const reply = ctx.message.reply_to_message;
    if (!reply) return ctx.reply('Reply to the user you wish to warn.');
    const chatId = ctx.chat.id;
    const userId = reply.from.id;
    if (!warnings[chatId]) warnings[chatId] = {};
    warnings[chatId][userId] = (warnings[chatId][userId] || 0) + 1;
    ctx.reply(`User ${userId} has been warned. Total warnings: ${warnings[chatId][userId]}.`);
    if (ctx.sendLog) {
      ctx.sendLog(`User ${userId} warned by ${ctx.from.username} in ${ctx.chat.title}. Total warnings: ${warnings[chatId][userId]}.`)
        .catch((err) => console.error('Logging error:', err));
    }
  });
};
