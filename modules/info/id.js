// modules/info/id.js
module.exports = (bot) => {
  bot.command('id', (ctx) => {
    let response = `Your ID: ${ctx.from.id}\n`;
    if (ctx.chat) {
      response += `Chat ID: ${ctx.chat.id}`;
    }
    ctx.reply(response);
  });
};
