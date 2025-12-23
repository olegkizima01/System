import time
from tui.messages import MessageBuffer, AgentType


def test_add_dedup():
    buf = MessageBuffer(max_messages=10)
    buf._dedupe_ttl = 0.1

    buf.add(AgentType.ATLAS, "[VOICE] Стартова ініціалізація завершена")
    assert len(buf.messages) == 1

    # immediate duplicate should be ignored
    buf.add(AgentType.ATLAS, "[VOICE] Стартова ініціалізація завершена")
    assert len(buf.messages) == 1

    # different agent with same text should be allowed
    buf.add(AgentType.TETYANA, "[VOICE] Стартова ініціалізація завершена")
    assert len(buf.messages) == 2

    # after ttl same agent can add again
    time.sleep(0.12)
    buf.add(AgentType.ATLAS, "[VOICE] Стартова ініціалізація завершена")
    assert len(buf.messages) == 3
    # duplicate counter should have counted one suppressed duplicate for ATLAS
    stats = buf.get_duplicate_stats()
    assert stats.get("atlas", 0) >= 1


def test_upsert_stream_dedup():
    buf = MessageBuffer(max_messages=10)
    buf._dedupe_ttl = 0.1

    buf.upsert_stream(AgentType.GRISHA, "[VOICE] Повідомлення отримано та зрозуміло")
    assert len(buf.messages) == 1

    # immediate duplicate (upsert) should be ignored
    buf.upsert_stream(AgentType.GRISHA, "[VOICE] Повідомлення отримано та зрозуміло")
    assert len(buf.messages) == 1

    # different agent allowed
    buf.upsert_stream(AgentType.ATLAS, "[VOICE] Повідомлення отримано та зрозуміло")
    assert len(buf.messages) == 2

    time.sleep(0.12)
    buf.upsert_stream(AgentType.GRISHA, "[VOICE] Повідомлення отримано та зрозуміло")
    assert len(buf.messages) == 3
    stats = buf.get_duplicate_stats()
    assert stats.get("grisha", 0) >= 1
