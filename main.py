from post_translator import post_translator

lang = 'en'
# lang = 'jp'
model = "axios"
# model = "veritas"
# model = "chatGPT4"
# model = "chatGPT4_bb"

def main():
    post_translator(lang, model)

if __name__ == '__main__':
    main()