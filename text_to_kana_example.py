from lib.en_to_jp import EnToJp

if __name__ == "__main__":
    en_to_jp = EnToJp()
    while True:
        text = input("文章中の英単語をカタカナに変換します。文章を入力してください。\n> ")
        print("alkana Only")
        print(f"    {en_to_jp.text_to_kana(text, True,False)}")
        print("japanglish Only")
        print(f"    {en_to_jp.text_to_kana(text, False,True, False)}")
        print("japanglish inference Only")
        print(f"    {en_to_jp.text_to_kana(text, False,True, True)}")
        print("alkana japanglish no inference")
        print(f"    {en_to_jp.text_to_kana(text, True,True,False)}")
        print("alkana japanglish inference")
        print(f"    {en_to_jp.text_to_kana(text, True,True,True)}")
