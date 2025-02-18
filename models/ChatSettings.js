const mongoose = require('mongoose');

const ChatSettingsSchema = new mongoose.Schema({
  chatId: { type: Number, required: true, unique: true },
  welcome: { type: String, default: '' },
  goodbye: { type: String, default: '' }
});

module.exports = mongoose.model('ChatSettings', ChatSettingsSchema);
