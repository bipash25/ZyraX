const { Telegraf } = require('telegraf');
const config = require('./config');
const loadModules = require('./loader');

const bot = new Telegraf(config.BOT_TOKEN);

// Basic commands for PM and group
bot.start((ctx) => ctx.reply('Welcome to ZyraX - The Ultimate Telegram Bot!'));
bot.command('help', (ctx) => {
  // This can be enhanced later to show a dynamic menu.
  ctx.reply('Help: Use /info, /ping, /id, /rules, and many more commands. For full details, visit our docs.');
});
bot.command('ping', (ctx) => ctx.reply('Pong!'));

// Load all modules dynamically
loadModules(bot);

// Global error handling
bot.catch((err, ctx) => {
  console.error(`Error for ${ctx.updateType}:`, err);
});

// Start the bot
bot.launch().then(() => {
  console.log('ZyraX is live!');
});