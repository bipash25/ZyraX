// modules/logging/logsettings.js
let logSettings = {}; // chatId -> settings object

module.exports = (bot) => {
  bot.command('logsettings', (ctx) => {
    const chatId = ctx.chat.id;
    const args = ctx.message.text.split(' ').slice(1);
    if (args.length === 0) {
      return ctx.reply(`Current log settings: ${JSON.stringify(logSettings[chatId] || {})}`);
    }
    // For demo, we set settings as key/value pairs.
    logSettings[chatId] = logSettings[chatId] || {};
    args.forEach(arg => {
      const [key, value] = arg.split('=');
      logSettings[chatId][key] = value;
    });
    ctx.reply(`Log settings updated: ${JSON.stringify(logSettings[chatId])}`);
  });
};
