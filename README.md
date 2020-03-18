# Functionality for constructing regular expressions

This package provides utility functions for constructing and matching Regular expressions as well as a number
of specific regexes, focussed mostly on information extraction from Spanish plain text.

# # The following regexes are currently implemented:
- CIF (Spanish company id nr)
- DNI (Spanish people id nr)
- email
- written dates (in Spanish)
- business type abbreviations from all over the world (e.g. B.V.B.A. or S.A. in Spain)
- Twitter hashtags and mentions
- Spanish names (based on a dictionary)
    => Uses a different technique, interwoven with spacy 


# # Implementation details

The way the specific regexes work (their functional scope) can be seen by looking at the unit tests (test_regexutils.py)

A new regex can be added by inheriting from the "RegexMatcher" class

The classes SingleWordRegexBuilder and MultiWordRegexBuilder can be used to create regexes. 
SingleWordRegexBuilder is used for regexes which match on a single "token". It contains functionality to create a regex based on a list of options
MultiWordRegexBuilder can create regexes which span multiple "tokens", and allows tokens to be optional
The big advantage of using these builders is that there is a single point of construction for the regexes. Currently there is logic for defining word separators (defining the tokenisation on the regex level), which also takes into account the fact that a word is not preceeded by a word separator if it starts the document, or followed by one if it ends it. If this code is adapted later on, all the regexes defined with it are immediately updated.
The SingleWordRegexBuilder can generate regexes which can be used in a MultiWordRegexBuilder by
using the build_as_part method.


# # Read the ISSUES file to get an idea of open issues with this project
# # Read the FEATURE_IDEAS file for some features which would be nice to add to the package (feel free to extend)
