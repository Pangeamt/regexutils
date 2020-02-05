import spacy
from spacy.tokens import Token
import unidecode  # GPL license
from spacy.tokens.doc import Doc
from spacy.tokens.span import Span


def main():
    file_name = "files/mini_names_file.txt"
    names_set = set()
    with open(file_name) as file:
        for line in file:
            names_set.add(line.strip())
    name_matcher = NameListMatcher(names_set)
    nlp = spacy.load("es_core_news_md")
    nlp.add_pipe(name_matcher, last=True)  # add last to the pipeline


def add_name_matching_to_nlp_pipeline(nlp):
    file_firsts = "files/spanish_first_names.txt"
    file_lasts = "files/spanish_last_names.txt"

    first_names_set_all = set()
    with open(file_firsts) as file:
        for line in file:
            first_names_set_all.add(line.strip())
    # Removing the names which consist of more than one name (eg. Maria Carmen)
    first_names_set = {name for name in first_names_set_all if len(name.split(" ")) == 1}
    first_name_matcher = FirstNameListMatcher(first_names_set)

    last_names_set_all = set()
    with open(file_lasts) as file:
        for line in file:
            last_names_set_all.add(line.strip())
    # Removing the names which consist of more than one name (eg. Maria Carmen)
    last_names_set = {name for name in last_names_set_all if len(name.split(" ")) == 1}
    last_name_matcher = LastNameListMatcher(last_names_set)
    full_name_matcher = FullNameMatcher()

    # Potential optimisation: remove accents once, then use this info in the NameListMatcher
    # To do so: change code in NameListMatcher to call the sin_accent custom extension and uncomment next 2 lines

    # accent_remover = AccentRemover()
    # nlp.add_pipe(accent_remover, last=True)
    nlp.add_pipe(first_name_matcher, last=True)
    nlp.add_pipe(last_name_matcher, last=True)
    nlp.add_pipe(full_name_matcher, last=True)

class NameListMatcher:

    def __init__(self, in_names, extension_name="is_name"):
        """names is an iterable of names where names consist of max 1 word (so no spaces)
        If there are names with spaces they will be removed from the set of names"""
        in_names_set = set(in_names)
        names = {AccentRemover.remove_accents(name.casefold()) for name in in_names_set if len(name.split(" ")) == 1}
        self.names = names
        self.extension_name = extension_name
        if not Token.has_extension(extension_name):
            Token.set_extension(extension_name, default=False)

    def __call__(self, doc):
        for token in doc:
            if AccentRemover.remove_accents(token.text.casefold()) in self.names:
                token._.set(self.extension_name, True)
        return doc  # don't forget to return the Doc!


class AccentRemover:
    def __init__(self, extension_name="sin_accents"):
        self.extension_name = extension_name
        if not Token.has_extension(extension_name):
            Token.set_extension(extension_name, default=False)

    def __call__(self, doc):
        for token in doc:
            accented_string = token.text
            token_sin_accents = self.remove_accents(accented_string)
            token._.set(self.extension_name, token_sin_accents)
        return doc

    @staticmethod
    def remove_accents(unicode_word):
        # From https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
        return unidecode.unidecode(unicode_word)


class FirstNameListMatcher(NameListMatcher):
    EXTENSION_NAME = "is_first_name"

    def __init__(self, in_names):
        super().__init__(in_names, self.EXTENSION_NAME)


class LastNameListMatcher(NameListMatcher):
    EXTENSION_NAME = "is_last_name"

    def __init__(self, in_names):
        super().__init__(in_names, self.EXTENSION_NAME)


class FullNameMatcher:
    TOKEN_EXTENSION_NAME = "full_name"
    SPAN_EXTENSION_NAME = "is_full_name"
    DOC_EXTENSION_NAME = "full_names"
    SPAN_LABEL = "full_name"
    ANOT_INIT = "B-PER"
    ANOT_OTHER = "I-PER"
    ANOT_NONE = "O"
    ABBREVIATIONS = ["D."]

    def __init__(self, first_name_extension_name=FirstNameListMatcher.EXTENSION_NAME,
                 last_name_extension_name=LastNameListMatcher.EXTENSION_NAME):

        self.token_extension_name = self.TOKEN_EXTENSION_NAME
        self.span_extension_name = self.SPAN_EXTENSION_NAME
        self.doc_extension_name = self.DOC_EXTENSION_NAME
        self.first_name_extension_name = first_name_extension_name
        self.last_name_extension_name = last_name_extension_name

        if not Token.has_extension(self.token_extension_name):
            Token.set_extension(self.token_extension_name, default=self.ANOT_NONE)
        if not Span.has_extension(self.span_extension_name):
            Span.set_extension(self.span_extension_name, getter=self.is_full_name_getter)
        if not Doc.has_extension(self.doc_extension_name):
            Doc.set_extension(self.doc_extension_name, default=[])

    def __call__(self, doc):
        # Could use refactoring for readability and structure, as it's too complex now
        full_name_spans = []
        min_span_size = 2
        max_span_size = 2

        is_first_char_capped_list = [doc[i].text[0].isupper() for i in range(len(doc))]

        i = 0
        while i < len(doc)-1:
            is_first_name_this = doc[i]._.get(self.first_name_extension_name)
            is_last_name_next = doc[i+1]._.get(self.last_name_extension_name)
            both_capped = is_first_char_capped_list[i] and is_first_char_capped_list[i+1]
            if is_first_name_this and is_last_name_next and both_capped:
                doc[i]._.set(self.token_extension_name, self.ANOT_INIT)
                doc[i+1]._.set(self.token_extension_name, self.ANOT_OTHER)
                new_span = Span(doc, i, i+1, label=self.SPAN_LABEL)
                span_start = i
                span_end = i+1

                #look-back for more first names
                first_first_name = i
                while first_first_name-1>= 0 and doc[first_first_name-1]._.get(self.first_name_extension_name)\
                        and is_first_char_capped_list[first_first_name-1]:
                    first_first_name -= 1
                span_start = first_first_name
                if first_first_name != i: #name starts earlier
                    doc[i]._.set(self.token_extension_name, self.ANOT_OTHER)
                    doc[first_first_name]._.set(self.token_extension_name, self.ANOT_INIT)
                    for j in range(first_first_name+1, i):
                        doc[first_first_name]._.set(self.token_extension_name, self.ANOT_OTHER)
                # Check if considering the last name as a first name would still yield a valid match
                #   when adding the following word
                look_ahead_counter = 1
                while (i+1+look_ahead_counter) < len(doc) \
                        and doc[i+look_ahead_counter]._.get(self.first_name_extension_name) \
                        and doc[i+1+look_ahead_counter]._.get(self.last_name_extension_name)\
                        and is_first_char_capped_list[i+1+look_ahead_counter]:
                    doc[i+1+look_ahead_counter]._.set(self.token_extension_name, self.ANOT_OTHER)
                    look_ahead_counter += 1
                    span_end += 1
                #Check if it can be extended with more last names
                while(span_end+1 < len(doc)
                        and doc[span_end+1]._.get(self.last_name_extension_name)
                        and is_first_char_capped_list[span_end+1]):
                    doc[span_end+1]._.set(self.token_extension_name, self.ANOT_OTHER)
                    span_end += 1
                full_name_spans.append(new_span)
                i = span_end+1
            else:
                i += 1

        doc._.set(self.doc_extension_name, full_name_spans)

        return doc

    def is_full_name_getter(self, tokens):
        if tokens is None or len(tokens) < 1:
            return False
        if tokens[0]._.get(self.token_extension_name) != self.ANOT_INIT:
            return False
        for token in tokens[1:]:
            if tokens[0]._.get(self.token_extension_name) != self.ANOT_OTHER:
                return False
        return True
