class TranslateObj:
    def __init__(self, sourceLangType, sourceLangText, targetLangType, room_id, author):
        self.__sourceLangType = sourceLangType
        self.__source = sourceLangText
        self.__targetLang = targetLangType
        self.room_id = room_id
        self.author = author
        self.started = False

    def get_source_content(self):
        return self.__source

    def get_targetLang_type(self):
        return self.__targetLang

    def get_source_type(self):
        return self.__sourceLangType


