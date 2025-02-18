exports.init = (bot) => {
  bot.command('promote', async (ctx) => {
    try {
      const reply = ctx.message.reply_to_message;
      if (!reply) return ctx.reply('Reply to the user you wish to promote.');
      await ctx.telegram.promoteChatMember(ctx.chat.id, reply.from.id, {
        can_change_info: true,
        can_delete_messages: true,
        can_invite_users: true,
        can_restrict_members: true,
        can_pin_messages: true,
        can_promote_members: false
      });
      ctx.reply(`User ${reply.from.id} promoted to admin.`);
    } catch (error) {
      console.error('Promote error:', error);
      ctx.reply('Promotion failed. Check my rights.');
    }
  });
};

exports.help = [
  { name: '/promote', description: 'Promote a user to admin.', category: 'ADMIN' }
];
