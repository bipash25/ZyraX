require('dotenv').config();

module.exports = {
  BOT_TOKEN: process.env.BOT_TOKEN,
  LOG_CHANNEL_ID: process.env.LOG_CHANNEL_ID,
  OWNER_ID: process.env.OWNER_ID,
  MONGO_URI: process.env.MONGO_URI,
  OPENWEATHER_API_KEY: process.env.OPENWEATHER_API_KEY
};
