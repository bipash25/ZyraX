const fs = require('fs');
const path = require('path');

function loadModules(bot, dir = path.join(__dirname, 'modules')) {
  fs.readdirSync(dir).forEach((fileOrDir) => {
    const fullPath = path.join(dir, fileOrDir);
    if (fs.statSync(fullPath).isDirectory()) {
      loadModules(bot, fullPath);
    } else if (fileOrDir.endsWith('.js')) {
      const moduleFn = require(fullPath);
      if (typeof moduleFn === 'function') {
        moduleFn(bot);
        console.log(`Loaded module: ${fullPath}`);
      }
    }
  });
}

module.exports = loadModules;
