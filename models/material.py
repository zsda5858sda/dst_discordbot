class Material(object):
    def __init__(self, index_list: list, title: str, kw: str, character_list: list):
        self._cur_index = 0
        self._limit = 10
        if isinstance(index_list, list) and isinstance(title, str) and isinstance(kw, str) and isinstance(character_list, list):
            self._index_list = index_list
            self._title = title
            self._kw = kw
            self._character_list = character_list
        else:
            self._index_list = []
            self._title = ''
            self._kw = ''
            self._character_list = []

    @property
    def index_list(self):
        return self._index_list

    @property
    def cur_index(self):   
        return self._cur_index

    @property
    def limit(self):
        return self._limit

    @property
    def title(self):
        return self._title

    @property
    def kw(self):
        return self._kw

    @index_list.setter
    def index_list(self, value):
        self._index_list = value
    
    @cur_index.setter
    def cur_index(self, value):
        self._cur_index = value

    @limit.setter
    def limit(self, value):
        self._limit = value

    @title.setter
    def title(self, value):
        self._title = value

    @kw.setter
    def kw(self, value):
        self._kw = value