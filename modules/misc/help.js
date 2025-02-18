const { helpRegistry } = require('../../loader');
exports.init = (bot) => {
  bot.command('help', (ctx) => {
    const categories = Object.keys(helpRegistry);
    if (categories.length === 0) return ctx.reply('No commands available.');
    const keyboard = categories.map(cat => ([{ text: cat.toUpperCase(), callback_data: `help_category_${cat}` }]));
    ctx.reply('Select a category to see its commands:', {
      reply_markup: {
        inline_keyboard: keyboard
      }
    });
  });

  bot.action(/help_category_(.+)/, (ctx) => {
    const category = ctx.match[1];
    if (!helpRegistry[category]) return ctx.answerCbQuery('No commands found.');
    const commands = helpRegistry[category];
    let msg = `*${category.toUpperCase()} Commands:*\n`;
    commands.forEach(cmd => {
      msg += `- ${cmd.name} - ${cmd.description}\n`;
    });
    ctx.editMessageText(msg, {
      parse_mode: 'Markdown',
      reply_markup: {
        inline_keyboard: [
          [{ text: '⬅️ Back', callback_data: 'help_back' }]
        ]
      }
    });
    ctx.answerCbQuery();
  });

  bot.action('help_back', (ctx) => {
    const categories = Object.keys(helpRegistry);
    const keyboard = categories.map(cat => ([{ text: cat.toUpperCase(), callback_data: `help_category_${cat}` }]));
    ctx.editMessageText('Select a category to see its commands:', {
      reply_markup: {
        inline_keyboard: keyboard
      }
    });
    ctx.answerCbQuery();
  });
};

exports.help = [
  { name: '/help', description: 'Display this help message with command categories.', category: 'MISC' }
];
