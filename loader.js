const fs = require('fs');
const path = require('path');
const chalk = require('chalk').default;

const helpRegistry = {};

function loadModules(bot, dir = path.join(__dirname, 'modules')) {
  fs.readdirSync(dir).forEach((fileOrDir) => {
    const fullPath = path.join(dir, fileOrDir);
    if (fs.statSync(fullPath).isDirectory()) {
      loadModules(bot, fullPath);
    } else if (fileOrDir.endsWith('.js')) {
      const mod = require(fullPath);
      if (typeof mod.init === 'function') {
        mod.init(bot);
      }
      if (Array.isArray(mod.help)) {
        mod.help.forEach((cmd) => {
          const category = cmd.category || 'UNCATEGORIZED';
          if (!helpRegistry[category]) helpRegistry[category] = [];
          helpRegistry[category].push({ name: cmd.name, description: cmd.description });
        });
        // Log a summary per category from this module
        const categories = new Set(mod.help.map(cmd => cmd.category || 'UNCATEGORIZED'));
        categories.forEach((cat) => {
          const count = mod.help.filter(cmd => (cmd.category || 'UNCATEGORIZED') === cat).length;
          console.log(chalk.green(`Loaded ${count} ${cat} command(s) from ${fullPath}`));
        });
      } else {
        console.log(chalk.gray(`Loaded module: ${fullPath}`));
      }
    }
  });
}

module.exports = { loadModules, helpRegistry };
