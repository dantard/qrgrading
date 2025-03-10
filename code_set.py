from code import Code


class CodeSet:
    def __init__(self):
        self.codes = []
        self.datas = set()

    def append(self, code):
        if code.data not in self.datas:
            self.codes.append(code)
            self.datas.add(code.data)

    def clear(self):
        self.codes = []
        self.datas = set()

    def __repr__(self):
        text = str()
        for code in self.codes:
            text += str(code) + "\n"
        return text

    def filter(self, **kwargs):
        filtered =  [x for x in self.codes if all(getattr(x, key) == value for key, value in kwargs.items())]
        result = CodeSet()
        for code in filtered:
            result.append(code)
        return result

class PageCodeSet(CodeSet):

    def __init__(self, codeset=None):
        super().__init__()
        if codeset is not None:
            self.codes = codeset.codes
            self.datas = codeset.datas

    def get_q(self):
        return next((x for x in self.codes if x.type == Code.TYPE_Q), None)

    def get_p(self):
        return next((x for x in self.codes if x.type == Code.TYPE_P), None)

    def get_page(self):
        source = self.get_p() or self.get_q()
        if source is not None:
            return source.page
        return None

    def get_exam_id(self):
        if len(self.codes) > 0:
            return self.codes[0].exam
        return None

    def get_date(self):
        if len(self.codes) > 0:
            return self.codes[0].date
        return None

