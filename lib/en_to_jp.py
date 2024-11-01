import csv
import os
import re
from typing import Tuple

import alkana
from pyjapanglish import Japanglish


class EnToJp(object):
    def __init__(self) -> None:
        self.japanglish = Japanglish()
        self.user_dict_list: Tuple[str, str] = []
        EN_TO_JP_DICT_PATH = (
            os.path.dirname(os.path.abspath(__file__))
            + "/../config/en_to_jp_fix_dict.csv"
        )
        if os.path.exists(EN_TO_JP_DICT_PATH):
            with open(EN_TO_JP_DICT_PATH, mode="r") as fix_dict_file:
                csv_reader = csv.reader(fix_dict_file)
                next(csv_reader)  # 1行目を無視
                for row in csv_reader:
                    if len(row) >= 2:
                        self.japanglish.user_dict[row[0]] = row[1]
                        self.user_dict_list.append((row[0], row[1]))

    def replace_english_to_alkana(self, text: str) -> str:
        """テキストに含まれている英単語をalkanaでカタカナに変換して返す

        Args:
            text (str): 変換対象のテキスト

        Returns:
            str: 変換後のテキスト
        """
        output = ""
        # 先頭から順番に英単語を検索しカタカナに変換
        while word := re.search(r"[a-zA-Z]{1,}", text):
            output += text[: word.start()] + self.word_to_alkana(word.group())
            text = text[word.end() :]
        return output + text

    def word_to_alkana(self, word: str) -> str:
        """英単語がカタカナに変換できる場合はカタカナにして返す

        Args:
            word (str): 変換対象の英単語

        Returns:
            str: 変換後のカタカナ
        """

        if kana := alkana.get_kana(word.lower()):
            # ユーザー辞書に登録されている場合はユーザー辞書の値を返す
            for user_dict in self.user_dict_list:
                if word.lower() == user_dict[0]:
                    return user_dict[1]
            return kana
        else:
            if re.fullmatch(r"(?:[A-Z][a-z]{1,}){2,}", word):
                m = re.match(r"[A-Z][a-z]{1,}", word)
                first = self.word_to_alkana(m.group())
                second = self.word_to_alkana(word[m.end() :])
                return first + second
            return word

    def replace_english_to_japanglish(self, text, inference: bool = False) -> str:
        """ "テキストに含まれている英単語をjapanglishでカタカナに変換して返す。3文字以上の文字数の単語が対象

        Args:
            text (str): 変換対象のテキスト
            inference (bool, optional): 変換できない場合に推論変換するかのフラグ。デフォルトはFalse。

        Returns:
            str: 変換後のテキスト
        """

        output = ""
        while word := re.search(r"[a-zA-Z]{3,}", text):
            output += text[: word.start()] + self.word_to_japanglish(
                word.group(), inference
            )
            text = text[word.end() :]
        return output + text

    def word_to_japanglish(self, word: str, inference: bool = False) -> str:
        """英単語がカタカナに変換できる場合はjapanglishでカタカナにして返す。3文字以上の文字数の単語が対象

        Args:
            word (str): 変換対象の英単語
            inference (bool, optional): 変換できない場合に推論変換するかのフラグ。デフォルトはFalse。

        Returns:
            str: 変換後のカタカナ
        """
        if self.japanglish.convert(word.lower(), inference) is not None:
            return self.japanglish.convert(word.lower(), inference)
        else:
            if re.fullmatch(r"(?:[A-Z][a-z]{3,}){2,}", word):
                m = re.match(r"[A-Z][a-z]{3,}", word)
                first = self.word_to_japanglish(m.group())
                second = self.word_to_japanglish(word[m.end() :])
                return first + second
            return word

    def text_to_kana(
        self,
        text: str,
        alkana: bool = True,
        japanglish: bool = True,
        inference: bool = False,
    ) -> str:
        """テキストに含まれている英単語をカタカナに変換して返す

        Args:
            text (str): 変換対象のテキスト
            alkana (bool, optional): alkanaで変換するかのフラグ。デフォルトはTrue。
            japanglish (bool, optional): japanglishで変換するかのフラグ。デフォルトはTrue。
            inference (bool, optional): 変換できない場合に推論変換するかのフラグ。デフォルトはFalse。

        Returns:
            str: 変換後のテキスト
        """
        if alkana:
            text = self.replace_english_to_alkana(text)
        if japanglish:
            text = self.replace_english_to_japanglish(text, inference)
        return text
