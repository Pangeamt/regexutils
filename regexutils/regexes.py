from regex import regex
import csv
import files
try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

class MultiWordRegexBuilder:
    """Build a regex across multiple words
    Follows a kind of builder pattern
    The resulting regex will match a series of words (as many words as there are individual regexes)
    Each word is separated from another word by 1 or potentially more "separators"
        (space, tab... Can be defined by user)
    A word can be made optional. If a word is optional, the regex matches it both if the word is present or not
    """
    #ToDo Note: there is currently a bug with making the first or last word optional.
    def __init__(self, separators=r"([\p{P}\s])", max_separators=3):
        """Take care to define the possible separators as a valid regex between square brackets
            (making them separate options), as in the standard value
            max_separators defines the maximal amount of separators allowed between separate words matched by the
            final multiword regex"""
        self._regex_words = []
        self._optionals = []
        self.separators = separators
        self.max_separators = max_separators

    def add_regex_word(self, regex_word, optional=False):
        self._regex_words.append(regex_word)
        self._optionals.append(optional)

    def build(self):
        if len(self._regex_words) == 0:
            return ""
        if self._optionals[0] == True:
            raise ValueError("The first argument of the regex cannot be optional (this is a temprary fix "
                             "to avoid a bug")
        if self._optionals[-1] == True:
            raise ValueError("The last argument of the regex cannot be optional (this is a temprary fix "
                             "to avoid a bug")

        # look behind: start of string or separator
        regex_start = "(?<=^|" + self.separators + ")("
        # Look ahead: end of string or separator. Any separator after the match is not consumed
        regex_end = ")(?=" + self.separators + "|$)"
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
        return self.build()


class SingleWordRegexBuilder:
    """Creates regexes which can be used to match individual words
    Contains functionality for the creation of disjunctive regexes: regexes which consist of a series of or-options
        Useful for example when creating a regex which matches any of a list of words (e.g. all countries in the world)
    """

    def __init__(self, word_sep_tokens=r"([\p{P}\s])"):
        """Take care to define the possible separators a valid regex between square brackets
            (making them separate options), as in the standard value"""
        self._possibilities = []
        self.separators = word_sep_tokens

    def build(self):
        """Returns the total regex, ensuring it only matches words and not subwords ("Hi" will match
        string "I say Hi" but not "I say Hiii" or "I say aHi"""
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


class RegexMatcher:
    """Class which stores a compiled regex and which can apply it to text and return a list of matches
    Extend this class to create specific classes which implement a regex
    The implementing subclass should pass its regex to this class's constructor (using super)
    It can be applied to a text by using the match method"""

    def __init__(self, matcher_regex):
        """matcher_regex must be a compiled regex"""
        self.matcher_regex = matcher_regex

    def match(self, text):
        """Applies a regex and returns a list of matches"""
        res_iter = self.matcher_regex.finditer(text)
        res = []
        for elem in res_iter:
            res.append(elem)
        return res


class CIFMatcher(RegexMatcher):

    def __init__(self):
        cif_regex_1 = r"[A-Z]\d{7,7}([A-Z]|\d)"
        cif_regex_2 = r"[A-Z]-\d\d\.\d{3,3}\.\d{3,3}"
        regex_builder = SingleWordRegexBuilder()
        regex_builder.add_option(cif_regex_1)
        regex_builder.add_option(cif_regex_2)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)


class DNIMatcher(RegexMatcher):

    def __init__(self):
        dni_regex_1 = r"\d{8,8}[A-Z]"
        dni_regex_2 = r"\d\d\.\d{3,3}\.\d{3,3}-[A-Z]"
        regex_builder = SingleWordRegexBuilder()
        regex_builder.add_option(dni_regex_1)
        regex_builder.add_option(dni_regex_2)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)


class EmailMatcher(RegexMatcher):

    def __init__(self):
        # based onhttps://www.regular-expressions.info/email.html
        email_regex = r"[A-Z\d\.\_%\+\-]+@[A-Z\d\.\-]+\.[A-Z]{2,}"
        regex_builder = SingleWordRegexBuilder()
        regex_builder.add_option(email_regex)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)


class DateMatcher(RegexMatcher):
    """Logic to find dates in Spanish texts
    """

    MONTHS_FILE_NAME = "spanish_months.txt"
    NRS_FILE_NAME = "spanish_numbers.txt"

    def __init__(self):
        self.written_numbers = self.read_numbers_file()
        self.months = self.read_months_file()

        day_nrs_regex = r"(([1-9])|(1[0-9])|(2[0-9])|(3[0-1]))"
        de_regex = "(de)"
        year_regex = r"((19[0-9][0-9])|(20[0-9][0-9]))"

        b = MultiWordRegexBuilder()
        wb1 = SingleWordRegexBuilder()
        wb1.add_list_options_as_regex(self.written_numbers)
        wb1.add_option(day_nrs_regex)
        b.add_regex_word(wb1.build_as_part())
        b.add_regex_word(de_regex, optional=True)
        wb3 = SingleWordRegexBuilder()
        wb3.add_list_options_as_regex(self.months)
        b.add_regex_word(wb3.build_as_part())
        b.add_regex_word(de_regex, optional=True)
        b.add_regex_word(year_regex)
        tot_regex = b.build()

        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)

    @classmethod
    def read_numbers_file(cls):
        nrs_file = pkg_resources.open_text(files, cls.NRS_FILE_NAME)
        written_numbers = []
        for line in nrs_file:
            written_numbers.append(line.strip())
        nrs_file.close()
        return written_numbers

    @classmethod
    def read_months_file(cls):
        months_file = pkg_resources.open_text(files, cls.MONTHS_FILE_NAME)
        months = []
        for line in months_file:
            months.append(line.strip())
        months_file.close()
        return months


class CompanyExtensionMatcher(RegexMatcher):
    """Logic to match business terminations from all over the world (like S.A., B.V.B.A.)"""
    COMPANY_EXTENSIONS = "bussiness_terminations.txt"
    def __init__(self):
        file = pkg_resources.open_text(files, self.COMPANY_EXTENSIONS)
        file_lines = file.readlines()
        file.close()
        companies = []
        for line in file_lines:
            companies.append(line.strip().replace(".", "\."))
        builder = SingleWordRegexBuilder()
        builder.add_list_options_as_regex(companies)
        comp_regex = builder.build()
        matcher_regex = regex.compile(comp_regex)
        super().__init__(matcher_regex)


class HashTagMatcher(RegexMatcher):
    """Matches twitter hashtags (#TAG)"""
    def __init__(self):
        ht_regex = r"[＃#]{1}(\w+)"
        regex_builder = SingleWordRegexBuilder()
        regex_builder.add_option(ht_regex)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)


class SpanishDemonstrativePronounsMatcher(RegexMatcher):
    # Source: https://www.spanishdict.com/guia/los-pronombres-demostrativos-en-ingles
    #   (verified by Yaiza for correctness)
    WORDS_TO_MATCH_LOWERCASED = [
        "sólo",

        "ésto",
        "ésta",
        "éstos",
        "éstas",

        "éste",

        "aquél",
        "aquéllo",
        "aquélla",
        "aquéllos",
        "aquéllas",

        "ése",
        "éso",
        "ésa",
        "ésas",
        "ésos",
    ]

    def __init__(self):
        regex_builder = SingleWordRegexBuilder(word_sep_tokens=r"([\p{P}\s])") #All punctuation and white space chars
        regex_builder.add_list_options_as_regex(self.WORDS_TO_MATCH_LOWERCASED)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)


class MentionMatcher(RegexMatcher):
    """Matches twitter mentions (@USERNAME)"""
    def __init__(self):
        mention_regex = r"[＠@]{1}([\w_]+)"
        regex_builder = SingleWordRegexBuilder()
        regex_builder.add_option(mention_regex)
        tot_regex = regex_builder.build()
        matcher_regex = regex.compile(tot_regex, flags=regex.IGNORECASE)
        super().__init__(matcher_regex)


