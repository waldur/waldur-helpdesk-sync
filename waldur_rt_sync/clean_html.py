import bleach

ALLOWED_TAGS = [
    "a",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    "p",
    "span",
    "u",
    "s",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "sub",
    "sup",
    "pre",
    "br",
]


ALLOWED_ATTRIBUTES = {
    "a": ["href"],
}


def clean_html(value):
    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )


def unescape_html(value):
    return value.replace('&lt;', '<').replace('&gt;', '>')
