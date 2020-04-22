import unittest

import spacy

from regexutils import spacyrules
from regexutils.spacyrules import NameListMatcher


class TestNameListMatcher(unittest.TestCase):
    TEST_NAMES_FILE = "../files/mini_names_file.txt"
    SPACY_MODEL_NAME = "es_core_news_sm"

    def test(self):
        examples = [
            "Jose y Begoña y Luís con accento",
            "jose y begoña pequenito"
            ]

        matches_list = [
            [True, False, True, False, True, False, False],
            [True, False, True, False]
            ]

        extension_name = "is_name"
        names_set = set()
        with open(self.TEST_NAMES_FILE) as file:
            for line in file:
                names_set.add(line.strip())
        name_matcher = NameListMatcher(names_set, extension_name)
        nlp = spacy.load(self.SPACY_MODEL_NAME)
        nlp.add_pipe(name_matcher, last=True)  # add last to the pipeline

        assert(len(matches_list) == len(examples))
        for i in range (len(examples)):
            example =examples[i]
            matches = matches_list[i]
            doc = nlp(example)
            assert len(doc) == len(matches)
            for j in range(len(doc)):
                assert doc[j]._.get(extension_name) == matches[j]

class TestFullNameMatcher(unittest.TestCase):

    def test(self):
        st_tag = spacyrules.FullNameMatcher.ANOT_INIT
        mid_tag = spacyrules.FullNameMatcher.ANOT_OTHER
        none_tag = spacyrules.FullNameMatcher.ANOT_NONE

        examples = {
            "Jose Luís Ferreira no es Jose Luís ní Luís Ferreira":
                [st_tag, mid_tag, mid_tag, none_tag, none_tag, st_tag, mid_tag, none_tag, st_tag, mid_tag],
            "Aguilar Ferreira": [none_tag, none_tag],  # Two last names without first
            "Jose Aguilar": [st_tag, mid_tag],
            "Jose Aguilar va a su huertito": [st_tag, mid_tag, none_tag, none_tag, none_tag, none_tag],
            "Ferreira está guay": [none_tag, none_tag, none_tag], #sole last name
            "Begoña sigue siempre": [none_tag, none_tag, none_tag], #sole first name
            "Su huerto vive":[none_tag, none_tag, none_tag], # Check if only caps are accepted.
                                                             # (su is valid first name and huerto valid last name)
            "jose Begoña Ferreira": [none_tag, st_tag, mid_tag],  # Check if only caps are accepted.
            "Begoña Yolanda Aguilar se extiende": [st_tag, mid_tag, mid_tag, none_tag, none_tag],
            "Jose Luís Luís Ferreira funciona": [st_tag, mid_tag, mid_tag, mid_tag, none_tag],
            "Jose Luís y Luís Jose": [st_tag, mid_tag, none_tag, st_tag, mid_tag],
            "Jose Maria Jose Maria": [st_tag, mid_tag, mid_tag, mid_tag] , # Both Jose and Maria are both first and
                                                                            # last name. Should match as a single name
            "Jose Luís Ferreira Yolanda": [st_tag, mid_tag, mid_tag, none_tag],
            "Jose Begoña Aguilar Ferreira se ha perdido":
                [st_tag, mid_tag, mid_tag, mid_tag, none_tag, none_tag, none_tag],
            # Title + last name not yet considered
            #"El gran D. Ferreira sigue" : [none_tag, none_tag, st_tag, mid_tag, none_tag]
        }

        nlp = spacy.load(TestNameListMatcher.SPACY_MODEL_NAME)
        spacyrules.add_name_matching_to_nlp_pipeline(nlp)


        for example, tags in examples.items():
            doc = nlp(example)
            assert len(doc) == len(tags)
            for j in range(len(tags)):
                # print(doc[j])
                # print(doc[j]._.get(spacyregex.FullNameMatcher.TOKEN_EXTENSION_NAME))
                # print(tags[j])
                assert(doc[j]._.get(spacyrules.FullNameMatcher.TOKEN_EXTENSION_NAME) == tags[j])







class TestSeparateMethods(unittest.TestCase):
    SPACY_MODEL_NAME = TestNameListMatcher.SPACY_MODEL_NAME

    def test_add_name_matching_to_nlp_pipeline(self):
        nlp = spacy.load(TestNameListMatcher.SPACY_MODEL_NAME)
        spacyrules.add_name_matching_to_nlp_pipeline(nlp)
        text = "Jose Aguilar y Begoña Ferreira"
        doc = nlp(text)
        matches_first = [True, False, False, True, False]
        matches_last = [True, True, False, True, True] #Jose and Begoña are also last names

        true_matches_first = [matches_first[i] == doc[i]._.is_first_name for i in range(0, len(doc))]
        true_matches_last = [matches_last[i] == doc[i]._.is_last_name for i in range(0, len(doc))]

        assert(len(doc) == len(matches_first) == len(matches_last))
        assert(False not in [matches_first[i] == doc[i]._.is_first_name for i in range(0, len(doc))])
        assert (False not in [matches_last[i] == doc[i]._.is_last_name for i in range(0, len(doc))])

class TestAccentRemover(unittest.TestCase):

    def test(self):
        nlp = spacy.load(TestNameListMatcher.SPACY_MODEL_NAME)
        extension_name = "sin_accents"
        accent_remover = spacyrules.AccentRemover(extension_name=extension_name)
        nlp.add_pipe(accent_remover)
        text = "Luís Begoña músen mosó"
        unaccented_words = ["Luis", "Begona", "musen", "moso"]
        doc = nlp(text)

        assert len(doc) == len(unaccented_words)
        for i in range(len(doc)):
            assert doc[i]._.get(extension_name) == unaccented_words[i]


if __name__ == '__main__':
    unittest.main()
