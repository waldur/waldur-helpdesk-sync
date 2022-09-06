import bleach

ALLOWED_TAGS = []

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
