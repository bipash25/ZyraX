// modules/admin/warnlimit.js
const warnLimits = {}; // chatId -> limit

module.exports = (bot) => {
  bot.command('warnlimit', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    const chatId = ctx.chat.id;
    if (args.length === 0) {
      const limit = warnLimits[chatId] || 3;
      return ctx.reply(`The current warning limit is ${limit}.`);
    }
    const newLimit = parseInt(args[0]);
    if (isNaN(newLimit)) return ctx.reply('Please provide a valid number.');
    warnLimits[chatId] = newLimit;
    ctx.reply(`Warning limit set to ${newLimit}.`);
  });
};
