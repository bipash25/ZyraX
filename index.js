const { Telegraf, session } = require('telegraf');
const config = require('./config');
const { loadModules, helpRegistry } = require('./loader');
const mongoose = require('mongoose');

mongoose.connect(config.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
}).then(() => {
  console.log('Connected to MongoDB.');
}).catch((err) => {
  console.error('MongoDB connection error:', err);
});

const bot = new Telegraf(config.BOT_TOKEN);
bot.use(session());

// Basic commands for both groups and private chats.
bot.start((ctx) => ctx.reply('Welcome to ZyraX - The Ultimate Telegram Bot!'));

// Load all command modules dynamically.
loadModules(bot);

bot.catch((err, ctx) => {
  console.error(`Error for ${ctx.updateType}:`, err);
});

bot.launch().then(() => {
  console.log('ZyraX is live!');
});
