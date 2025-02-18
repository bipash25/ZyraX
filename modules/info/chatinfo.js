exports.init = (bot) => {
  bot.command('chatinfo', (ctx) => {
    try {
      const chat = ctx.chat;
      const info = `*Chat Title:* ${chat.title || 'N/A'}\n*Type:* ${chat.type}\n*Chat ID:* ${chat.id}`;
      ctx.replyWithMarkdown(info);
    } catch (error) {
      console.error('Chatinfo error:', error);
      ctx.reply('Failed to get chat info.');
    }
  });
};

exports.help = [
  { name: '/chatinfo', description: 'Get information about the current chat.', category: 'INFO' }
];
