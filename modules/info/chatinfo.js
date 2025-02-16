// modules/info/chatinfo.js
module.exports = (bot) => {
    bot.command('chatinfo', (ctx) => {
      const chat = ctx.chat;
      const info = `Chat Title: ${chat.title || 'N/A'}\nType: ${chat.type}\nID: ${chat.id}`;
      ctx.reply(info);
    });
  };
  