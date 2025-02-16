const { Telegraf } = require('telegraf');
const config = require('./config');
const loadModules = require('./loader');
// require('dotenv').config();

const bot = new Telegraf(config.BOT_TOKEN);
// const bot = new Telegraf(process.env.BOT_TOKEN);

// Basic commands for both groups and private chats.
bot.start((ctx) => ctx.reply('Welcome to ZyraX - The Ultimate Telegram Bot!'));

// Load all command modules dynamically.
loadModules(bot);

// Global error handler.
bot.catch((err, ctx) => {
  console.error(`Error for ${ctx.updateType}:`, err);
});

// Launch the bot.
bot.launch().then(() => {
  console.log('ZyraX is live!');
});
