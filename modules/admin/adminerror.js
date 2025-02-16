// modules/admin/adminerror.js
let adminErrorEnabled = {}; // chatId -> boolean

module.exports = (bot) => {
  bot.command('adminerror', (ctx) => {
    const chatId = ctx.chat.id;
    const arg = ctx.message.text.split(' ')[1];
    if (!arg) return ctx.reply('Usage: /adminerror <on/off>');
    adminErrorEnabled[chatId] = arg.toLowerCase() === 'on';
    ctx.reply(`Admin error messages ${adminErrorEnabled[chatId] ? 'enabled' : 'disabled'}.`);
  });
};
