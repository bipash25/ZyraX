// modules/info/userinfo.js
module.exports = (bot) => {
    bot.command('userinfo', (ctx) => {
      const reply = ctx.message.reply_to_message;
      const user = reply ? reply.from : ctx.from;
      const info = `Name: ${user.first_name} ${user.last_name || ''}\nUsername: ${user.username || 'N/A'}\nID: ${user.id}`;
      ctx.reply(info);
    });
  };
  