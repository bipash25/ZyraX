const { Telegraf } = require('telegraf');
const config = require('./config');

// Importing modules
const moderation = require('./modules/moderation');
const fun = require('./modules/fun');
const customCommands = require('./modules/customCommands');
const logging = require('./modules/logging');

const bot = new Telegraf(config.BOT_TOKEN);

// Basic start command
bot.start((ctx) => ctx.reply('Welcome to ZyraX - The Ultimate Telegram Bot!'));

// Load core modules
moderation(bot);
fun(bot);
customCommands(bot);
logging(bot);

// Global error handling
bot.catch((err, ctx) => {
  console.error(`Error encountered for ${ctx.updateType}`, err);
});

// Launch the bot
bot.launch().then(() => {
  console.log('ZyraX is up and running!');
});