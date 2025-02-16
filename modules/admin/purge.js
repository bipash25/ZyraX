// modules/admin/purge.js
module.exports = (bot) => {
    // /purge when replied to a message deletes messages from that message to current message.
    bot.command('purge', async (ctx) => {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Please reply to the starting message to purge.');
      const fromMessageId = reply.message_id;
      const toMessageId = ctx.message.message_id;
      const chatId = ctx.chat.id;
      let count = 0;
      for (let i = fromMessageId; i <= toMessageId; i++) {
        try {
          await ctx.telegram.deleteMessage(chatId, i);
          count++;
        } catch (e) {
          // Skip messages that cannot be deleted.
        }
      }
      ctx.reply(`Purged ${count} messages.`);
    });
  };
  