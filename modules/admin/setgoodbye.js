const ChatSettings = require('../../models/ChatSettings');
exports.init = (bot) => {
  bot.command('setgoodbye', async (ctx) => {
    try {
      const args = ctx.message.text.split(' ').slice(1);
      if (args.length === 0) return ctx.reply('Usage: /setgoodbye <message>');
      const goodbyeMsg = args.join(' ');
      const chatId = ctx.chat.id;
      let settings = await ChatSettings.findOne({ chatId });
      if (!settings) {
        settings = new ChatSettings({ chatId });
      }
      settings.goodbye = goodbyeMsg;
      await settings.save();
      ctx.reply('Goodbye message updated.');
    } catch (error) {
      console.error('SetGoodbye error:', error);
      ctx.reply('Failed to set goodbye message.');
    }
  });

  bot.on('left_chat_member', async (ctx) => {
    try {
      const chatId = ctx.chat.id;
      const settings = await ChatSettings.findOne({ chatId });
      if (settings && settings.goodbye) {
        const goodbyeText = settings.goodbye.replace('{first}', ctx.message.left_chat_member.first_name);
        ctx.reply(goodbyeText);
      }
    } catch (error) {
      console.error('Goodbye on leave error:', error);
    }
  });
};

exports.help = [
  { name: '/setgoodbye', description: 'Set a custom goodbye message for when members leave.', category: 'ADMIN' }
];
