from regex import regex


class MultiWordRegexBuilder:
    """Build a regex across multiple words
    Follows a kind of builder pattern
    The resulting regex will match a series of words (as many words as there are individual regexes)
    Each word is separated from another word by 1 or potentially more "separators"
        (space, tab... Can be defined by user)
    A word can be made optional. It a word is optional, the regex matches it both if the word is present or not
    """
    def __init__(self, separators=r"([\p{P} \n\t])", max_separators=3):
        self._regex_words = []
        self._optionals = []
        self.separators = separators
        self.max_separators = max_separators

    def add_regex_word(self, regex_word, optional=False):
        self._regex_words.append(regex_word)
        self._optionals.append(optional)

    def create_total_regex(self):
        if len(self._regex_words) == 0:
            return ""
        regex_start = "(?<=^|" + self.separators + ")(" #look behind
        regex_end = ")(?=" + self.separators + "|$)" #Look ahead: any punctuation after the match is not consumed
        separator_str = self.separators + "{1," + str(self.max_separators) + "}"
        res = regex_start
        for i in range(0, len(self._regex_words) - 1):
            word_regex = self._regex_words[i]
            if self._optionals[i]:
                res += "(" + word_regex + separator_str + ")" + "?"
            else:
                res += word_regex + separator_str
        res += self._regex_words[-1]
        if self._optionals[-1]:
            res += "?"
        res += regex_end
        return res

    def __str__(self):
        return self.create_total_regex()


class RegexBuilder:
    """Creates regexes which can be used to match individual words
    Contains functionality for the creation of disjunctive regexes: regexes which consist of a series of or-options
        Useful for example when creating a regex which matches any of a list of words (e.g. all countries in the world)
    """

    def __init__(self, word_sep_tokens=r"\p{P} \n\t"):
        self._possibilities = []
        self.separators = "[" + word_sep_tokens + "]"

    def build(self):
        """Returns the total regex, extending it to ensure it only matches starting from the start of a word
            or ending with the end of the word if specified"""
        if len(self._possibilities) == 0:
            return ""
        regex_start = "(?<=^|" + self.separators + ")(" #look behind
        regex_end = ")(?=" + self.separators + "|$)" #Look ahead: any punctuation after the match is not consumed
        if len(self._possibilities) == 1:
            return regex_start + self._possibilities[0] + regex_end
        res = regex_start
        for i in range(0, len(self._possibilities)-1):
            pos = self._possibilities[i]
            res += "(" + pos + ")" + "|"
        res += "(" + self._possibilities[-1] + ")" + regex_end
        return res

    def build_as_part(self):
        """Returns the total regex as is, without taking into account whether or not it starts at the beginning
        of a word and ends at the end of a word"""
        if len(self._possibilities) == 0:
            return ""
        if len(self._possibilities) == 1:
            return self._possibilities[0]
        res = "("
        for i in range(0, len(self._possibilities)-1):
            pos = self._possibilities[i]
            res += pos + "|"
        res += "(" + self._possibilities[-1] + "))"
        return res

    def add_option(self, new_regex):
        self._possibilities.append(new_regex)

    def add_list_options_as_regex(self, options):
        to_add = self.gen_list_options_as_regex(options)
        self._possibilities.append(to_add)

    @staticmethod
    def gen_list_options_as_regex(options):
        res = r"("
        first = True
        for option in options:
            if not first:
                res += "|"
            res = res + option
            first = False
        res += ")"
        return res

class RegexMatcher():
    """Class which stores a compiled regex and which can apply it to text
    Extend this class to create specific classes which implement a regex
    The implementing subclass should pass its regex to this class's constructor (using super)
    It can be applied to a text by using the match method"""

    def __init__(self, matcher_regex):
        """matcher_regex must be a compiled regex"""
        self.matcher_regex = matcher_regex

    def match(self, text):
        res_iter = self.matcher_regex.finditer(text)
        res = []
        for elem in res_iter:
            res.append(elem)
        return res

class CIFMatcher(RegexMatcher):

    def __init__(self):
        cif_regex_1 = r"[A-Z]\d{7,7}([A-Z]|\d)"
        cif_regex_2 = r"[A-Z]-\d\d\.\d{3,3}\.\d{3,3}"
        regex_builder = RegexBuilder()
        regex_builder.add_option(cif_regex_1)
        regex_builder.add_option(cif_regex_2)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)

class DNIMatcher(RegexMatcher):

    def __init__(self):
        dni_regex_1 = r"\d{8,8}[A-Z]"
        dni_regex_2 = r"\d\d\.\d{3,3}\.\d{3,3}-[A-Z]"
        regex_builder = RegexBuilder()
        regex_builder.add_option(dni_regex_1)
        regex_builder.add_option(dni_regex_2)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)

class EmailMatcher(RegexMatcher):

    def __init__(self):
        # based onhttps://www.regular-expressions.info/email.html
        email_regex = "[A-Z\d\.\_%\+\-]+@[A-Z\d\.\-]+\.[A-Z]{2,}"
        regex_builder = RegexBuilder()
        regex_builder.add_option(email_regex)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)


class DateMatcher(RegexMatcher):
    """Logic to find dates in Spanish texts
    """

    MONTHS_FILE_LOC = "Files/Spanish_months"
    NRS_FILE_LOC = "Files/Spanish_numbers"

    def __init__(self):
        nrs_file = open(self.NRS_FILE_LOC)
        written_numbers = []
        for line in nrs_file:
            written_numbers.append(line.strip())
        self.written_numbers = written_numbers
        nrs_file.close()

        months_file = open(self.MONTHS_FILE_LOC)
        months = []
        for line in months_file:
            months.append(line.strip())
        self.months = months
        months_file.close()

        day_nrs_regex = r"(([1-9])|(1[0-9])|(2[0-9])|(3[0-1]))"
        de_regex = "(de)"
        year_regex = r"((19[0-9][0-9])|(20[0-9][0-9]))"

        b = MultiWordRegexBuilder()
        wb1 = RegexBuilder()
        wb1.add_list_options_as_regex(written_numbers)
        wb1.add_option(day_nrs_regex)
        b.add_regex_word(wb1.build_as_part())
        b.add_regex_word(de_regex, optional=True)
        wb3 = RegexBuilder()
        wb3.add_list_options_as_regex(months)
        b.add_regex_word(wb3.build_as_part())
        b.add_regex_word(de_regex, optional=True)
        b.add_regex_word(year_regex)
        tot_regex = b.create_total_regex()

        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)


