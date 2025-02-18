exports.init = (bot) => {
  bot.command('purge', async (ctx) => {
    try {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Please reply to the starting message for purge.');
      const fromMessageId = reply.message_id;
      const toMessageId = ctx.message.message_id;
      const chatId = ctx.chat.id;
      let count = 0;
      for (let id = fromMessageId; id <= toMessageId; id++) {
        try {
          await ctx.telegram.deleteMessage(chatId, id);
          count++;
        } catch (e) {
          // Skip messages that cannot be deleted.
        }
      }
      ctx.reply(`Purged ${count} messages.`);
    } catch (error) {
      console.error('Purge error:', error);
      ctx.reply('Failed to purge messages.');
    }
  });
};

exports.help = [
  { name: '/purge', description: 'Delete messages from a starting replied message to the current message.', category: 'ADMIN' }
];
