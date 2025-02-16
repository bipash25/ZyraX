const fs = require('fs');
const path = require('path');

function loadModules(bot, dir = path.join(__dirname, 'modules')) {
  fs.readdirSync(dir).forEach((fileOrDir) => {
    const fullPath = path.join(dir, fileOrDir);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      loadModules(bot, fullPath);  // Recursively load subfolders
    } else if (fileOrDir.endsWith('.js')) {
      const commandModule = require(fullPath);
      if (typeof commandModule === 'function') {
        commandModule(bot);
        console.log(`Loaded module: ${fullPath}`);
      }
    }
  });
}

module.exports = loadModules;