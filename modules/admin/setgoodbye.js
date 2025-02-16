// modules/admin/setgoodbye.js
const goodbyes = {}; // chatId -> goodbye message

module.exports = (bot) => {
  bot.command('setgoodbye', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    if (args.length === 0) return ctx.reply('Usage: /setgoodbye <message>');
    const chatId = ctx.chat.id;
    goodbyes[chatId] = args.join(' ');
    ctx.reply('Goodbye message updated.');
  });

  // On member leaving, send goodbye.
  bot.on('left_chat_member', (ctx) => {
    const chatId = ctx.chat.id;
    if (goodbyes[chatId]) {
      ctx.reply(goodbyes[chatId].replace('{first}', ctx.message.left_chat_member.first_name));
    }
  });
};
