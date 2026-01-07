#!/usr/bin/env python3
"""
Manual test runner for Phase 1 changes.
Tests the detect_topic_change function without requiring pytest.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

# Import the function we want to test
from src.agent.orchestrator_agent import detect_topic_change
from src.database.models import MessageRole


def test_detect_topic_change_with_correction_phrase():
    """Test that detect_topic_change identifies explicit user corrections"""
    print("Test 1: Correction phrase detection...")
    now = datetime.now(timezone.utc)
    messages = [
        MagicMock(
            content="Let's discuss the SSE feed",
            timestamp=now - timedelta(minutes=5),
            role=MessageRole.USER,
        ),
        MagicMock(
            content="Sure, the SSE feed needs...",
            timestamp=now - timedelta(minutes=4),
            role=MessageRole.ASSISTANT,
        ),
        MagicMock(
            content="but we weren't discussing the SSE feed",
            timestamp=now,
            role=MessageRole.USER,
        ),
    ]

    result = detect_topic_change(messages, "but we weren't discussing the SSE feed")
    assert result is True, "Should detect correction phrase"
    print("  ✓ Correction phrase detected correctly")


def test_detect_topic_change_with_new_topic_phrase():
    """Test that detect_topic_change identifies 'let's discuss' phrases"""
    print("Test 2: New topic phrase detection...")
    now = datetime.now(timezone.utc)
    messages = [
        MagicMock(
            content="Previous topic", timestamp=now - timedelta(minutes=5), role=MessageRole.USER
        ),
        MagicMock(
            content="Response", timestamp=now - timedelta(minutes=4), role=MessageRole.ASSISTANT
        ),
        MagicMock(content="lets discuss something else", timestamp=now, role=MessageRole.USER),
    ]

    result = detect_topic_change(messages, "lets discuss something else")
    assert result is True, "Should detect 'lets discuss' phrase"
    print("  ✓ New topic phrase detected correctly")


def test_detect_topic_change_with_time_gap():
    """Test that detect_topic_change identifies time gaps >1 hour"""
    print("Test 3: Time gap detection...")
    now = datetime.now(timezone.utc)
    messages = [
        MagicMock(
            content="Old message",
            timestamp=now - timedelta(hours=2),
            role=MessageRole.USER,
        ),
        MagicMock(
            content="New message after time gap",
            timestamp=now,
            role=MessageRole.USER,
        ),
    ]

    result = detect_topic_change(messages, "New message after time gap")
    assert result is True, "Should detect time gap >1 hour"
    print("  ✓ Time gap detected correctly")


def test_detect_topic_change_no_change():
    """Test that detect_topic_change returns False for normal conversation"""
    print("Test 4: Normal conversation (no change)...")
    now = datetime.now(timezone.utc)
    messages = [
        MagicMock(
            content="Let's discuss feature X",
            timestamp=now - timedelta(minutes=5),
            role=MessageRole.USER,
        ),
        MagicMock(
            content="Sure, feature X needs...",
            timestamp=now - timedelta(minutes=4),
            role=MessageRole.ASSISTANT,
        ),
        MagicMock(
            content="And also what about Y?",
            timestamp=now,
            role=MessageRole.USER,
        ),
    ]

    result = detect_topic_change(messages, "And also what about Y?")
    assert result is False, "Should NOT detect topic change in normal conversation"
    print("  ✓ Normal conversation handled correctly")


def test_detect_topic_change_handles_naive_timestamps():
    """Test that detect_topic_change handles timezone-naive timestamps"""
    print("Test 5: Naive timestamp handling...")
    now = datetime.now()  # Naive timestamp
    messages = [
        MagicMock(
            content="Old message",
            timestamp=now - timedelta(hours=2),
            role=MessageRole.USER,
        ),
        MagicMock(
            content="New message",
            timestamp=now,
            role=MessageRole.USER,
        ),
    ]

    # Should not crash with naive timestamps
    result = detect_topic_change(messages, "New message")
    assert result is True, "Should handle naive timestamps and detect time gap"
    print("  ✓ Naive timestamps handled correctly")


def test_all_correction_phrases():
    """Test all correction phrases from the implementation"""
    print("Test 6: All correction phrases...")
    now = datetime.now(timezone.utc)

    correction_phrases = [
        "but we weren't discussing",
        "but we werent discussing",
        "we were talking about",
        "not about that",
        "different topic",
        "let's discuss",
        "lets discuss",
        "switching topics",
        "new topic",
        "back to",
    ]

    for phrase in correction_phrases:
        messages = [
            MagicMock(
                content="Previous", timestamp=now - timedelta(minutes=1), role=MessageRole.USER
            ),
            MagicMock(
                content=f"Test message with {phrase} something",
                timestamp=now,
                role=MessageRole.USER,
            ),
        ]
        result = detect_topic_change(messages, f"Test message with {phrase} something")
        assert result is True, f"Should detect phrase: {phrase}"

    print(f"  ✓ All {len(correction_phrases)} correction phrases work correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1 Manual Test Suite")
    print("Testing: detect_topic_change() function")
    print("=" * 60)
    print()

    try:
        test_detect_topic_change_with_correction_phrase()
        test_detect_topic_change_with_new_topic_phrase()
        test_detect_topic_change_with_time_gap()
        test_detect_topic_change_no_change()
        test_detect_topic_change_handles_naive_timestamps()
        test_all_correction_phrases()

        print()
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print()
        print("Phase 1 implementation verified:")
        print("  ✓ Topic change detection working")
        print("  ✓ Correction phrase recognition working")
        print("  ✓ Time gap detection working")
        print("  ✓ Normal conversation handling working")
        print()

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Unexpected error: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
        exit(1)
