// modules/misc/help.js
module.exports = (bot) => {
    bot.command('help', (ctx) => {
      const helpText = `
  *ZyraX - Help*
  
  *Info & Utility:*
  • /help – This help message
  • /ping – Check bot latency
  • /id – Get your ID and chat ID
  • /userinfo – Get user information
  • /chatinfo – Get chat information
  • /stats – Bot statistics
  • /time – Current server time
  • /weather <city> – Get weather info
  
  *Fun & Games:*
  • /roll – Roll a dice
  • /coinflip – Flip a coin
  • /8ball – Magic 8-ball answers
  • /trivia – Start a trivia game
  • /rps <choice> – Rock-Paper-Scissors game
  • /guessword – Unscramble a word
  
  *Admin Commands:*
  • /ban – Ban a user
  • /kick – Kick a user
  • /mute – Mute a user
  • /warn – Warn a user
  • /warnlimit – Set/check warning limit
  • /setwelcome – Set welcome message
  • /setgoodbye – Set goodbye message
  • /antiflood – Configure antiflood
  • /lock /unlock – Lock or unlock items
  • /purge – Purge messages
  • /report – Report a user
  • /antiraid – Anti-raid settings
  • /promote – Promote a user
  • /demote – Demote a user
  • /adminlist – List admins
  • /admincache – Refresh admin cache
  • /anonadmin – Toggle anonymous admin usage
  • /adminerror – Toggle admin error messages
  
  *Owner Commands:*
  • /broadcast – Broadcast message to all subscribers
  • /eval – Evaluate JavaScript code
  • /restart – Restart the bot
  • /shutdown – Shutdown the bot
  • /dbbackup – Backup the database
  • /update – Update the bot
  
  More features coming soon.
      `;
      ctx.replyWithMarkdown(helpText);
    });
  };
  