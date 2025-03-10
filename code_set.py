from code import Code


class CodeSet:
    def __init__(self):
        self.codes = {}

    def append(self, code):
        self.codes[code.data] = code

    def clear(self):
        self.codes.clear()

    def __repr__(self):
        text = str()
        for code in self.codes.values():
            text += str(code) + "\n"
        return text

    def filter(self, **kwargs):
        filtered =  [x for x in self.codes.values() if all(getattr(x, key) == value for key, value in kwargs.items())]
        result = CodeSet()
        for code in filtered:
            result.append(code)
        return result


class PageCodeSet(CodeSet):

    def __init__(self, codeset=None):
        super().__init__()
        if codeset is not None:
            self.codes = codeset.codes

    def get_q(self):
        return next((x for x in self.codes.values() if x.type == Code.TYPE_Q), None)

    def get_p(self):
        return next((x for x in self.codes.values() if x.type == Code.TYPE_P), None)

    def get_page(self):
        source = self.get_p() or self.get_q()
        if source is not None:
            return source.page
        return None

    def get_exam_id(self):
        if len(self.codes.values()) > 0:
            return next(iter(self.codes.values())).exam
        return None

    def get_date(self):
        if len(self.codes.values()) > 0:
            return next(iter(self.codes.values())).date
        return None

