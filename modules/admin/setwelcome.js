const ChatSettings = require('../../models/ChatSettings');
exports.init = (bot) => {
  bot.command('setwelcome', async (ctx) => {
    try {
      const args = ctx.message.text.split(' ').slice(1);
      if (args.length === 0) return ctx.reply('Usage: /setwelcome <message>');
      const welcomeMsg = args.join(' ');
      const chatId = ctx.chat.id;
      let settings = await ChatSettings.findOne({ chatId });
      if (!settings) {
        settings = new ChatSettings({ chatId });
      }
      settings.welcome = welcomeMsg;
      await settings.save();
      ctx.reply('Welcome message updated.');
    } catch (error) {
      console.error('SetWelcome error:', error);
      ctx.reply('Failed to set welcome message.');
    }
  });

  bot.on('new_chat_members', async (ctx) => {
    try {
      const chatId = ctx.chat.id;
      const settings = await ChatSettings.findOne({ chatId });
      if (settings && settings.welcome) {
        const welcomeText = settings.welcome.replace('{first}', ctx.message.new_chat_members[0].first_name);
        ctx.reply(welcomeText);
      }
    } catch (error) {
      console.error('Welcome on join error:', error);
    }
  });
};

exports.help = [
  { name: '/setwelcome', description: 'Set a custom welcome message for new members.', category: 'ADMIN' }
];
