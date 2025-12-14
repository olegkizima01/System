from __future__ import annotations

from typing import Any, Callable

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.data_structures import Point
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.widgets import Frame

_app_state = {"instance": None}

def force_ui_update():
    app = _app_state.get("instance")
    if app:
        try:
            app.invalidate()
        except Exception:
            pass


def build_app(
    *,
    get_header: Callable[[], Any],
    get_context: Callable[[], Any],
    get_logs: Callable[[], Any],
    get_log_cursor_position: Callable[[], Point],
    get_menu_content: Callable[[], Any],
    get_input_prompt: Callable[[], Any],
    get_prompt_width: Callable[[], int],
    get_status: Callable[[], Any],
    input_buffer: Buffer,
    show_menu: Condition,
    kb: KeyBindings,
    style: BaseStyle,
) -> Application:
    header_window = Window(FormattedTextControl(get_header), height=1, style="class:header")

    context_window = Window(FormattedTextControl(get_context), style="class:context")

    log_window = Window(
        FormattedTextControl(get_logs, get_cursor_position=get_log_cursor_position),
        wrap_lines=True,
    )

    menu_window = Window(FormattedTextControl(get_menu_content), style="class:menu")

    input_area = VSplit(
        [
            Window(
                FormattedTextControl(get_input_prompt),
                width=lambda: get_prompt_width(),
                style="class:input",
                dont_extend_width=True,
            ),
            Window(BufferControl(buffer=input_buffer), style="class:input"),
        ]
    )

    def get_status_text() -> AnyFormattedText:
        return get_status()

    status_window = Window(FormattedTextControl(get_status_text), height=1, style="class:status")

    main_body = HSplit(
        [
            Frame(header_window, style="class:frame.border"),
            VSplit(
                [
                    Frame(log_window, title="LOG", style="class:frame.border"),
                    ConditionalContainer(
                        Frame(
                            context_window,
                            title="КОНТЕКСТ",
                            style="class:frame.border",
                            width=Dimension(min=40, max=55),
                        ),
                        filter=Condition(lambda: not show_menu()),
                    ),
                    ConditionalContainer(
                        Frame(
                            menu_window,
                            title="MENU",
                            style="class:frame.border",
                            width=Dimension(min=45, max=70),
                        ),
                        filter=show_menu,
                    ),
                ]
            ),
            Frame(input_area, style="class:frame.border", height=3),
            status_window,
        ]
    )

    app = Application(layout=Layout(main_body), key_bindings=kb, full_screen=True, style=style)
    
    # Store global reference for UI updates
    _app_state["instance"] = app
    
    return app
