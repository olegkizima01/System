"""Compatibility wrapper.

The i18n implementation lives in `tui/i18n.py`.
This module re-exports the public API to avoid breaking existing imports.
"""

from tui.i18n import (  # noqa: F401
    DEFAULT_LANG,
    LANGUAGE_NAMES,
    TOP_LANGS,
    TRANSLATIONS,
    lang_name,
    normalize_lang,
    tr,
)
