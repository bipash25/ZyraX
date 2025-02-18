const axios = require('axios');
const config = require('../../config');
exports.init = (bot) => {
  bot.command('weather', async (ctx) => {
    try {
      const parts = ctx.message.text.split(' ').slice(1);
      if (parts.length === 0) return ctx.reply('Usage: /weather <city>');
      const city = parts.join(' ');
      const response = await axios.get(`http://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&appid=${config.OPENWEATHER_API_KEY}&units=metric`);
      const data = response.data;
      const msg = `Weather in ${data.name}, ${data.sys.country}:\n${data.weather[0].description}\nTemp: ${data.main.temp}°C\nFeels Like: ${data.main.feels_like}°C\nHumidity: ${data.main.humidity}%`;
      ctx.reply(msg);
    } catch (error) {
      console.error('Weather error:', error);
      ctx.reply('Could not fetch weather. Please check the city name.');
    }
  });
};

exports.help = [
  { name: '/weather', description: 'Get current weather for a city.', category: 'INFO' }
];
