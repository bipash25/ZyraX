// A simple in-memory store for custom commands.
const customCommandsStore = {};

module.exports = (bot) => {
  // Command to add a custom command.
  // Usage: /addcmd trigger message
  bot.command('addcmd', (ctx) => {
    const parts = ctx.message.text.split(' ');
    if (parts.length < 3) {
      return ctx.reply('Usage: /addcmd <trigger> <message>');
    }
    const trigger = parts[1];
    const message = parts.slice(2).join(' ');
    customCommandsStore[trigger] = message;
    ctx.reply(`Custom command added: when someone says "${trigger}", I will reply with "${message}"`);
  });

  // Listener for custom commands: if a message exactly matches a trigger.
  bot.on('text', (ctx, next) => {
    const text = ctx.message.text;
    if (customCommandsStore[text]) {
      return ctx.reply(customCommandsStore[text]);
    }
    return next();
  });
};