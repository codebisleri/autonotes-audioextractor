from deep_translator import GoogleTranslator

def translate_text(text, target_lang='hi'):
    return GoogleTranslator(source='auto', target=target_lang).translate(text)
