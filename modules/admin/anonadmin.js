// modules/admin/anonadmin.js
let anonAdminEnabled = {}; // chatId -> boolean

module.exports = (bot) => {
  bot.command('anonadmin', (ctx) => {
    const chatId = ctx.chat.id;
    const arg = ctx.message.text.split(' ')[1];
    if (!arg) return ctx.reply('Usage: /anonadmin <on/off>');
    anonAdminEnabled[chatId] = arg.toLowerCase() === 'on';
    ctx.reply(`Anonymous admin ${anonAdminEnabled[chatId] ? 'enabled' : 'disabled'}.`);
  });
};
