const config = require('../config');

module.exports = (bot) => {
  // Function to send logs to the specified log channel.
  function sendLog(message) {
    if (config.LOG_CHANNEL_ID && config.LOG_CHANNEL_ID !== 'YOUR_LOG_CHANNEL_ID') {
      bot.telegram.sendMessage(config.LOG_CHANNEL_ID, message);
    }
  }

  // Example: /logs command (placeholder for displaying logs)
  bot.command('logs', (ctx) => {
    ctx.reply('Displaying logs is not implemented yet.');
  });

  // Example: logging each incoming message (this is optional and for debugging)
  bot.on('message', (ctx, next) => {
    // Uncomment below to log every message.
    // sendLog(`New message from ${ctx.from.username}: ${ctx.message.text}`);
    next();
  });

  // Expose the sendLog function on the bot context for use in other modules.
  bot.context.sendLog = sendLog;
};