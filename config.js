require('dotenv').config();

module.exports = {
  BOT_TOKEN: process.env.BOT_TOKEN,
  // Log channel: if not set, logging commands will simply do nothing.
  LOG_CHANNEL_ID: process.env.LOG_CHANNEL_ID,
  WAPI_KEY: process.env.WEATHER_API_KEY
};
