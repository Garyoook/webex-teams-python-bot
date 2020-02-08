class TranslateObj:
    def __init__(self, source, targetLang, room_id, author):
        self.source = source
        self.targetLang = targetLang
        self.room_id = room_id
        self.author = author
        self.started = False

    def get_source_content(self):
        return self.source

    def get_target(self):
        return self.targetLang


    def set_source_content(self, source):
        self.source = source;

