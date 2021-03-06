import unittest

from regexutils import regexes
from regex import regex
from regexutils.regexes import DateMatcher, CIFMatcher, DNIMatcher, SingleWordRegexBuilder, RegexMatcher, EmailMatcher


class TestRegexBuilder(unittest.TestCase):
    """Most of SingleWordRegexBuilder is tested by testing some of its implementing classes.
    Here are tested codepaths which were at the time of writing the tests not covered by the implementing classes
    """

    def test_build(self):
        """Tests code path with 0 options given"""
        rb = SingleWordRegexBuilder()
        assert rb.build() == ""
        rb.add_option("and")
        rb.add_option("BLABLABALBABLABLABA")

        and_regex_text = rb.build()
        and_regex = regex.compile(and_regex_text)
        matcher = RegexMatcher(and_regex)
        examples = [
            "and", "and ", " and", "this and that"
        ]
        negative_examples = ["andy", " andy ", " rand "]

        for example in examples:
            res = matcher.match(example)
            assert len(res) == 1

        for example in negative_examples:
            assert len(matcher.match(example)) == 0


class TestMultiWordRegexBuilder(unittest.TestCase):
    def test(self):
        rb = regexes.MultiWordRegexBuilder()
        rb.add_regex_word("Hello", optional=True)
        with self.assertRaises(ValueError):
            rb.build()

        rb = regexes.MultiWordRegexBuilder()
        rb.add_regex_word("Hello", optional=False)
        rb.add_regex_word("Again", optional=True)
        with self.assertRaises(ValueError):
            rb.build()
        try:
            rb = regexes.MultiWordRegexBuilder()
            rb.add_regex_word("Hello", optional=False)
            rb.add_regex_word("Once", optional=True)
            rb.add_regex_word("Again", optional=False)
            rb.build()
        except ValueError:
            self.fail("ValueError thrown in TestMultiWordRegexBuilder which should not happen")


class TestDateMatcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.matcher = DateMatcher()

    def test_init(self):
        matcher = DateMatcher()
        months = [month.casefold() for month in matcher.months]
        numbers = [number.casefold() for number in matcher.written_numbers]
        assert ("diciembre".casefold() in months)
        assert ("veintiséis".casefold() in numbers)

    def test_read_numbers_file(self):
        numbers = DateMatcher.read_numbers_file()
        assert numbers is not None
        assert ("veintiséis" in numbers)


    def test_read_months_file(self):
        months = DateMatcher.read_months_file()
        assert months is not None
        assert ("Diciembre" in months)

    def test_find_dates(self):
        examples = [
            "Quedamos el lunes 4 de noviembre de 2019 a las 4 en plaza de la virgen",
            "Nos vemos el cuatro de enero de 1905 para arreglar las cosas",
            "sin des: 4 enero 1905 para arreglar las cosas",
            "4 de noviembre de 2019 inicia un frase",
            "También puede terminarlo: 4 de noviembre de 2019",
            "O llevar punctuación: 4 de noviembre de 2019!",
            r"O hay más espacios y otros tipos de punctuación: 4  de---noviembre de /2019\!",
            "No sensitvo al case 4  DE noViemBre de 2019 "

        ]

        negative_examples = ["Nos vemos los 3 en deciembre algun día a las 4",
                             "En 2019 agosto los 2020 quedaron",
                             "Demasiado punctuación entre los caracteres: 4----de noviembre de 2019",
                             "Error de ortografia: 4 de novimbre de 2019"
                             ]

        for example in examples:
            res = self.matcher.match(example)
            assert len(res) == 1

        for example in negative_examples:
            assert len(self.matcher.match(example)) == 0

        # Checking that the date is matched exactly, without superfluous punctuation and spaces around it
        ex = " ¿4 de noviembre de 2018? "
        match = self.matcher.match(ex)[0].captures()[0]  # Potentially stupid code, found very ad hoc
        assert match == "4 de noviembre de 2018"


class TestCIFMatcher(unittest.TestCase):
    def test_find_CIFs(self):

        examples = [
            "Este es un CIF A-14.010.342 ",
            "Un numero que vale B97017461 es este",
            "Y uno más complicado, con punctuacion al final: B97017461!",
            "B97017461 Y qué pasa si empieza el frase? ",
            "O lo termina? B97017461",
            "Case no importa: a-14.010.342 "

        ]
        neg_examples = [
            "y otro que no X78951234315 ",
            "Y tampoco: 123456789 ",
            "Ni BB97017461 ",
            "Haciendo el esplit en otro parte del número hace incorrecto el número: A-140.10.342 ",
            "O olvidar un esplit: A140.10.342 ",
            "No DNI: 50.083.695-E "

        ]
        matcher = CIFMatcher()

        for example in examples:
            assert len(matcher.match(example)) == 1

        for example in neg_examples:
            assert len(matcher.match(example)) == 0

        ex = " ¿B97017461? "
        assert (len(matcher.match(ex)) == 1)
        match = matcher.match(ex)[0].captures()[0]  # Potentially stupid code, found very ad hoc
        assert match == "B97017461"


class TestDNIMatcher(unittest.TestCase):
    def test(self):
        examples = [
            "Este es un DNI 50.083.695-E ",
            "Un numero que vale 50083695E es este",
            "Y uno más complicado, con punctuacion al final: 50.083.695-E!",
            "50.083.695-E Y qué pasa si empieza el frase? ",
            "O lo termina? 50.083.695-E",
            "Case da igual 50.083.695-e ",

        ]
        neg_examples = [
            "y otro que no X78951234315",
            "Y tampoco: 123456789",
            "Ni BB97017461",
            "CIFs no: A-14.010.342"
            "Splitting at other parts of the DNI makes it invalid: 500.83.695-E "
        ]
        matcher = DNIMatcher()

        for example in examples:
            assert len(matcher.match(example)) == 1

        for example in neg_examples:
            assert len(matcher.match(example)) == 0


class TestEmailMatcher(unittest.TestCase):
    def test(self):

        examples = [
            "Este es un correo: h.degroote@pangeanic.com ",
            "También: h_degroote@pangeanic.sales.info.es",
            "con punctuación: h.degroote@pangeanic.com."

        ]
        neg_examples = [
            "no soy correo: find out more @info ",
        ]
        matcher = EmailMatcher()

        for example in examples:
            assert len(matcher.match(example)) == 1

        for example in neg_examples:
            assert len(matcher.match(example)) == 0

class TestCompanyExtensionsMatcher(unittest.TestCase):
    def test(self):
        examples = [
            "Pangeanic BVBA ",
            "Pangea S.A. "
        ]
        matcher = regexes.CompanyExtensionMatcher()
        for example in examples:
            assert len(matcher.match(example)) == 1


class TestHashTagMatcher(unittest.TestCase):
    def test(self):
        matcher = regexes.HashTagMatcher()
        text = "Hi #PaNíwrevña_2! And welcome"
        res = matcher.match(text)
        assert len(res) == 1
        assert text[res[0].span()[0]:res[0].span()[1]] == "#PaNíwrevña_2"



class TestMentionMatcher(unittest.TestCase):
    def test(self):
        matcher = regexes.MentionMatcher()
        text = "Hi @Hañz_í... and welcome"
        res = matcher.match(text)
        assert len(res) == 1
        assert text[res[0].span()[0]:res[0].span()[1]] == "@Hañz_í"

        text = "Hi h.degroote@pangeanic.com"
        res = matcher.match(text)
        assert len(res) == 0



if __name__ == '__main__':
    unittest.main()
