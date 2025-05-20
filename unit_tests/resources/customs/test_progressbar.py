import pytest

import logging

from resources.customs import ProgressBar


def ends_with_color_reset(message: str) -> bool:
    return message.endswith("\033[0m")


def ends_with_color_reset_and_carriage_return(message: str) -> bool:
    return message.endswith("\033[0m" + "\033[F")


def starts_with_green(message: str) -> bool:
    return message.startswith('\033[32m')


def starts_with_light_blue(message: str) -> bool:
    return message.startswith('\033[94m')


def get_original_message(message: str) -> str:
    # remove unimportant timestamps and stuff
    message = message.split("[INFO]: ", 2)[1]
    message = message.split("\x1b[0m", 1)[0]
    return message


def test_begin(caplog):
    # Arrange
    progressbar = ProgressBar(4)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.begin("a b c")

    message = caplog.messages[0]

    # Assert
    assert starts_with_light_blue(message), \
        f"Message '{message}' was not light blue."
    assert ends_with_color_reset_and_carriage_return(message), \
        (f"Message '{message}' did not end with a color reset and "
         f"carriage return.")

    # Act
    message = get_original_message(message)

    # Assert
    assert "[+   ]: a b c" == message


def test_complete(caplog):
    # Arrange
    progressbar = ProgressBar(5)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.complete("b c d")

    message = caplog.messages[0]

    # Assert
    assert starts_with_green(message), \
        f"Message '{message}' was not green."
    assert ends_with_color_reset(message), \
        f"Message '{message}' did not end with a color reset (and newline)."

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#    ]: b c d" == message


def test_begin_newline(caplog):
    # Arrange
    progressbar = ProgressBar(4)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.begin("a b c", newline=True)

    message = caplog.messages[0]

    # Assert
    assert starts_with_light_blue(message), \
        f"Message '{message}' was not light blue."
    assert ends_with_color_reset(message), \
        f"Message '{message}' did not end with a color reset (and newline)."

    # Act
    message = get_original_message(message)

    # Assert
    assert "[+   ]: a b c" == message


def test_complete_no_newline(caplog):
    # Arrange
    progressbar = ProgressBar(5)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.complete("b c d", newline=False)

    message = caplog.messages[0]

    # Assert
    assert starts_with_green(message), \
        f"Message '{message}' was not green."
    assert ends_with_color_reset_and_carriage_return(message), \
        (f"Message '{message}' did not end with a color reset and "
         f"carriage return.")

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#    ]: b c d" == message


def test_complete_complete(caplog):
    # Arrange
    progressbar = ProgressBar(5)
    progressbar.complete("")

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.complete("")

    message = caplog.messages[0]

    # Assert
    assert starts_with_green(message), \
        f"Message '{message}' was not green."
    assert ends_with_color_reset(message), \
        f"Message '{message}' did not end with a color reset (and newline)."

    # Act
    message = get_original_message(message)

    # Assert
    assert "[##   ]: " == message


# noinspection DuplicatedCode
def test_complete_begin(caplog):
    # Arrange
    progressbar = ProgressBar(5)
    progressbar.complete("")

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.begin("")

    message = caplog.messages[0]

    # Assert
    assert starts_with_light_blue(message), \
        f"Message '{message}' was not green."
    assert ends_with_color_reset_and_carriage_return(message), \
        (f"Message '{message}' did not end with a color reset and "
         f"carriage return.")

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#+   ]: " == message


# noinspection DuplicatedCode
def test_begin_begin(caplog):
    # Arrange
    progressbar = ProgressBar(5)
    progressbar.begin("")

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.begin("")

    message = caplog.messages[0]

    # Assert
    assert starts_with_light_blue(message), \
        f"Message '{message}' was not green."
    assert ends_with_color_reset_and_carriage_return(message), \
        (f"Message '{message}' did not end with a color reset and "
         f"carriage return.")

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#+   ]: " == message


def test_begin_complete(caplog):
    # Arrange
    progressbar = ProgressBar(5)
    progressbar.begin("")

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.complete("")

    message = caplog.messages[0]

    # Assert
    assert starts_with_green(message), \
        f"Message '{message}' was not green."
    assert ends_with_color_reset(message), \
        f"Message '{message}' did not end with a color reset (and newline)."

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#    ]: " == message


def test_padding_length(caplog):
    # Arrange
    progressbar = ProgressBar(9)
    progressbar.begin("qwerty" * 3)
    expected_progress_bar = "[#+       ]: "

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.begin("")

    message = get_original_message(caplog.messages[0])
    expected_output = expected_progress_bar + " " * len("qwerty") * 3

    # Assert
    assert expected_output == message


def test_short_bar_complete(caplog):
    # Arrange
    progressbar = ProgressBar(1)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.complete("")

    message = get_original_message(caplog.messages[0])

    # Assert
    assert "[#]: " == message


def test_short_bar_begin(caplog):
    # Arrange
    progressbar = ProgressBar(1)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.begin("")

    message = get_original_message(caplog.messages[0])

    # Assert
    assert "[+]: " == message


def test_short_bar_begin_complete(caplog):
    # Arrange
    progressbar = ProgressBar(1)
    progressbar.begin("")
    # Act
    with caplog.at_level(logging.INFO):
        progressbar.complete("")

    message = get_original_message(caplog.messages[0])

    # Assert
    assert "[#]: " == message


def test_progress_overflow(caplog):
    # Arrange
    progressbar = ProgressBar(1)
    progressbar.complete("")

    # Assert
    with pytest.raises(OverflowError):
        progressbar.complete("")
