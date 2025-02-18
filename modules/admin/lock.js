const locks = {}; // locks[chatId] = Set of locked items.
exports.init = (bot) => {
  bot.command('lock', (ctx) => {
    try {
      const args = ctx.message.text.split(' ').slice(1);
      if (args.length === 0) return ctx.reply('Usage: /lock <item1> [item2] ...');
      const chatId = ctx.chat.id;
      if (!locks[chatId]) locks[chatId] = new Set();
      args.forEach(item => locks[chatId].add(item.toLowerCase()));
      ctx.reply(`Locked items: ${Array.from(locks[chatId]).join(', ')}`);
    } catch (error) {
      console.error('Lock error:', error);
      ctx.reply('Error locking items.');
    }
  });

  bot.command('unlock', (ctx) => {
    try {
      const args = ctx.message.text.split(' ').slice(1);
      if (args.length === 0) return ctx.reply('Usage: /unlock <item1> [item2] ...');
      const chatId = ctx.chat.id;
      if (!locks[chatId]) return ctx.reply('No items are locked.');
      args.forEach(item => locks[chatId].delete(item.toLowerCase()));
      ctx.reply(`Remaining locked items: ${Array.from(locks[chatId]).join(', ') || 'None'}`);
    } catch (error) {
      console.error('Unlock error:', error);
      ctx.reply('Error unlocking items.');
    }
  });

  bot.on('message', async (ctx, next) => {
    try {
      const chatId = ctx.chat.id;
      if (locks[chatId] && ctx.message.text) {
        const text = ctx.message.text.toLowerCase();
        if (locks[chatId].has('links') && text.includes('http')) {
          await ctx.deleteMessage();
          return;
        }
      }
    } catch (error) {
      console.error('Lock middleware error:', error);
    }
    return next();
  });
};

exports.help = [
  { name: '/lock', description: 'Lock certain message types (e.g., links).', category: 'ADMIN' },
  { name: '/unlock', description: 'Unlock locked message types.', category: 'ADMIN' }
];
