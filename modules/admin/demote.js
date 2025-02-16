// modules/admin/demote.js
module.exports = (bot) => {
    bot.command('demote', async (ctx) => {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Reply to the admin you wish to demote.');
      try {
        await ctx.telegram.promoteChatMember(ctx.chat.id, reply.from.id, {
          can_change_info: false,
          can_delete_messages: false,
          can_invite_users: false,
          can_restrict_members: false,
          can_pin_messages: false,
          can_promote_members: false
        });
        ctx.reply(`User ${reply.from.id} has been demoted.`);
      } catch (error) {
        ctx.reply('Failed to demote. Check my permissions.');
      }
    });
  };
  