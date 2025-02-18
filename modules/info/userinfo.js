exports.init = (bot) => {
  bot.command('userinfo', (ctx) => {
    try {
      const reply = ctx.message.reply_to_message;
      const user = reply ? reply.from : ctx.from;
      const info = `*Name:* ${user.first_name} ${user.last_name || ''}\n*Username:* ${user.username || 'N/A'}\n*ID:* ${user.id}`;
      ctx.replyWithMarkdown(info);
    } catch (error) {
      console.error('Userinfo error:', error);
      ctx.reply('Failed to get user info.');
    }
  });
};

exports.help = [
  { name: '/userinfo', description: 'Get information about a user.', category: 'INFO' }
];
