// modules/admin/setwelcome.js
const welcomes = {}; // chatId -> welcome message

module.exports = (bot) => {
  bot.command('setwelcome', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    if (args.length === 0) return ctx.reply('Usage: /setwelcome <message>');
    const chatId = ctx.chat.id;
    welcomes[chatId] = args.join(' ');
    ctx.reply('Welcome message updated.');
  });

  // On new chat member, send welcome message.
  bot.on('new_chat_members', (ctx) => {
    const chatId = ctx.chat.id;
    if (welcomes[chatId]) {
      ctx.reply(welcomes[chatId].replace('{first}', ctx.message.new_chat_members[0].first_name));
    }
  });
};
