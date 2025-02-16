// modules/admin/mute.js
module.exports = (bot) => {
    bot.command('mute', async (ctx) => {
      const reply = ctx.message.reply_to_message;
      const args = ctx.message.text.split(' ').slice(1);
      if (!reply) return ctx.reply('Reply to the user you wish to mute.');
      const targetId = reply.from.id;
      const durationSec = parseInt(args[0] || '60'); // default: 60 seconds
      try {
        await ctx.telegram.restrictChatMember(ctx.chat.id, targetId, {
          permissions: { can_send_messages: false },
          until_date: Math.floor(Date.now() / 1000) + durationSec
        });
        ctx.reply(`User ${targetId} muted for ${durationSec} seconds.`);
      } catch (error) {
        ctx.reply('Failed to mute the user.');
      }
    });
  };
  