# Multi-language support for ZyraX
# This is a simple i18n implementation

TRANSLATIONS = {
    "en": {
        "welcome": "Welcome to {chatname}, {mention}!",
        "goodbye": "Goodbye, {first}!",
        "banned": "{mention} has been banned.",
        "unbanned": "{mention} has been unbanned.",
        "kicked": "{mention} has been kicked.",
        "muted": "{mention} has been muted.",
        "unmuted": "{mention} has been unmuted.",
        "warned": "{mention} has been warned. Count: {count}/3",
        "warn_removed": "Removed warn for {mention}. Current count: {count}",
        "warns_reset": "Reset all warns for {mention}.",
        "no_permission": "You don't have permission to do that.",
        "user_not_found": "User not found.",
        "error": "An error occurred: {error}",
        "success": "Success!",
        "filter_saved": "Saved filter `{name}`.",
        "filter_deleted": "Stopped filter `{name}`.",
        "note_saved": "Saved note `{name}`.",
        "note_deleted": "Deleted note `{name}`.",
        "rules_set": "Rules have been set.",
        "no_rules": "No rules set for this chat.",
        "captcha_enabled": "Captcha verification enabled.",
        "captcha_disabled": "Captcha verification disabled.",
        "economy_balance": "{name}'s Balance: {balance} coins",
        "economy_daily": "Daily Claimed! You received {amount} coins!",
        "economy_work": "You worked as a {job} and earned {amount} coins!",
        "game_correct": "Correct! {mention} wins!",
        "game_wrong": "Wrong! Try again.",
        "music_playing": "Now Playing: {title}",
        "music_paused": "Paused.",
        "music_resumed": "Resumed.",
        "music_stopped": "Stopped playback.",
        "queue_empty": "Queue is empty.",
    },
    "es": {
        "welcome": "Bienvenido a {chatname}, {mention}!",
        "goodbye": "Adios, {first}!",
        "banned": "{mention} ha sido baneado.",
        "unbanned": "{mention} ha sido desbaneado.",
        "kicked": "{mention} ha sido expulsado.",
        "muted": "{mention} ha sido silenciado.",
        "unmuted": "{mention} ha sido desilenciado.",
        "warned": "{mention} ha sido advertido. Conteo: {count}/3",
        "no_permission": "No tienes permiso para hacer eso.",
        "user_not_found": "Usuario no encontrado.",
        "error": "Ocurrio un error: {error}",
        "success": "Exito!",
        "economy_balance": "Balance de {name}: {balance} monedas",
        "music_playing": "Reproduciendo: {title}",
        "queue_empty": "La cola esta vacia.",
    },
    "pt": {
        "welcome": "Bem-vindo ao {chatname}, {mention}!",
        "goodbye": "Tchau, {first}!",
        "banned": "{mention} foi banido.",
        "unbanned": "{mention} foi desbanido.",
        "kicked": "{mention} foi expulso.",
        "muted": "{mention} foi silenciado.",
        "unmuted": "{mention} foi desmutado.",
        "warned": "{mention} foi avisado. Contagem: {count}/3",
        "no_permission": "Voce nao tem permissao para isso.",
        "user_not_found": "Usuario nao encontrado.",
        "error": "Ocorreu um erro: {error}",
        "success": "Sucesso!",
    },
    "hi": {
        "welcome": "{chatname} mein aapka swagat hai, {mention}!",
        "goodbye": "Alvida, {first}!",
        "banned": "{mention} ko ban kar diya gaya.",
        "unbanned": "{mention} ko unban kar diya gaya.",
        "no_permission": "Aapke paas iska permission nahi hai.",
        "user_not_found": "User nahi mila.",
        "success": "Safalta!",
    },
    "ru": {
        "welcome": "Dobro pozhalovat v {chatname}, {mention}!",
        "goodbye": "Do svidaniya, {first}!",
        "banned": "{mention} zabanen.",
        "unbanned": "{mention} razbanen.",
        "no_permission": "U vas net prav.",
        "user_not_found": "Polzovatel ne najden.",
        "success": "Uspeh!",
    }
}

def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """Get translated text with variable substitution"""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_dict.get(key) or TRANSLATIONS["en"].get(key, key)
    
    try:
        return text.format(**kwargs)
    except KeyError:
        return text

def get_available_languages() -> list:
    """Get list of available language codes"""
    return list(TRANSLATIONS.keys())

def get_language_name(code: str) -> str:
    """Get human-readable language name"""
    names = {
        "en": "English",
        "es": "Espanol",
        "pt": "Portugues",
        "hi": "Hindi",
        "ru": "Russkiy",
    }
    return names.get(code, code.upper())
