import pytest

from bite.io import ParserBuffer
from bite.parsers import (
    CaselessLiteral,
    CharacterSet,
    Literal,
    OneOf,
    ParsedCharacterSet,
    ParsedLiteral,
    ParsedOneOf,
    UnmetExpectationError,
)
from bite.tests.mock_reader import MockReader


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_buf,grammar,expected",
    [
        # Literals
        (
            b"LITERAL foo",
            Literal(b"LITERAL", name="literal"),
            ParsedLiteral("literal", b"LITERAL", 0, 7),
        ),
        (
            b"LiTeRaL foo",
            CaselessLiteral(b"lItErAl", name="literal"),
            ParsedLiteral("literal", b"lItErAl", 0, 7),
        ),
        # CharacterSet
        (
            b"123",
            CharacterSet(b"0123456789", name="charset"),
            ParsedCharacterSet("charset", b"1", 0, 1),
        ),
        (
            b"ABC",
            CharacterSet(b"0123456789", invert=True, name="inverted charset"),
            ParsedCharacterSet("inverted charset", b"A", 0, 1),
        ),
        # OneOf
        (
            b"A foo",
            OneOf([Literal(b"A"), Literal(b"B")]),
            ParsedOneOf(None, ParsedLiteral("b'A'", b"A", 0, 1), 0),
        ),
        (
            b"B foo",
            OneOf([Literal(b"A"), Literal(b"B")]),
            ParsedOneOf(None, ParsedLiteral("b'B'", b"B", 0, 1), 1),
        ),
        (
            b"A foo",
            OneOf(
                [Literal(b"A", name="first"), Literal(b"A", name="second")],
                name="precedence test",
            ),
            ParsedOneOf("precedence test", ParsedLiteral("first", b"A", 0, 1), 0),
        ),
    ],
)
async def test_successful_parsing(input_buf, grammar, expected):
    buffer = ParserBuffer(MockReader(input_buf))
    assert await grammar.parse(buffer) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_buf,grammar",
    [
        (b"foo", Literal(b"LITERAL")),
        (b"C", OneOf([Literal(b"A"), Literal(b"B")])),
        (b"A", CharacterSet(b"0123456789")),
        (b"0", CharacterSet(b"0123456789", invert=True)),
    ],
)
async def test_parsing_failure(input_buf, grammar):
    buffer = ParserBuffer(MockReader(input_buf))
    with pytest.raises(UnmetExpectationError) as excinfo:
        await grammar.parse(buffer)
    assert excinfo.value.expected == grammar
    assert excinfo.value.at_loc == 0


def test_parsed_one_of_loc_range():
    parsed_one_of = ParsedOneOf(None, ParsedLiteral(None, b"val", 4, 7), 0)
    assert parsed_one_of.start_loc == 4
    assert parsed_one_of.end_loc == 7
