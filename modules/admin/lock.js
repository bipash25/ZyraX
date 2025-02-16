// modules/admin/lock.js
const locks = {}; // chatId -> set of locked items

module.exports = (bot) => {
  bot.command('lock', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    if (args.length === 0) return ctx.reply('Usage: /lock <item1> [item2] ...');
    const chatId = ctx.chat.id;
    if (!locks[chatId]) locks[chatId] = new Set();
    args.forEach(item => locks[chatId].add(item.toLowerCase()));
    ctx.reply(`Locked items: ${Array.from(locks[chatId]).join(', ')}`);
  });

  bot.command('unlock', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    if (args.length === 0) return ctx.reply('Usage: /unlock <item1> [item2] ...');
    const chatId = ctx.chat.id;
    if (!locks[chatId]) return ctx.reply('No items are locked.');
    args.forEach(item => locks[chatId].delete(item.toLowerCase()));
    ctx.reply(`Remaining locked items: ${Array.from(locks[chatId]).join(', ') || 'None'}`);
  });

  // Middleware to delete locked items.
  bot.on('message', (ctx, next) => {
    const chatId = ctx.chat.id;
    if (locks[chatId]) {
      const text = ctx.message.text || '';
      // Example: block messages containing "http" (links) if locked.
      if (locks[chatId].has('links') && text.includes('http')) {
        return ctx.deleteMessage().catch(() => {});
      }
      // Similarly, you could check for stickers, GIFs, etc.
    }
    return next();
  });
};
