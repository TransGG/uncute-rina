import pytest

import logging

from resources.customs.progressbar import ProgressBar


def ends_with_color_reset(message: str) -> bool:
    return message.endswith("\033[0m")


def ends_with_color_reset_and_carriage_return(message: str) -> bool:
    return message.endswith("\033[0m" + "\033[F")


def starts_with_green(message: str) -> bool:
    return message.startswith('\033[32m')


def starts_with_light_blue(message: str) -> bool:
    return message.startswith('\033[94m')


def get_original_message(message: str) -> str:
    message = message.split("[INFO]: ", 2)[1]  # remove unimportant timestamps and stuff
    message = message.split("\x1b[0m", 1)[0]
    return message


def test_progress(caplog):
    # Arrange
    progressbar = ProgressBar(4)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.progress("a b c")

    message = caplog.messages[0]

    # Assert
    assert starts_with_light_blue(message), f"Message '{message}' was not light blue."
    assert ends_with_color_reset_and_carriage_return(message), (f"Message '{message}' did not end with a "
                                                                f"color reset and carriage return.")

    # Act
    message = get_original_message(message)

    # Assert
    assert "[+   ]: a b c" == message


def test_step(caplog):
    # Arrange
    progressbar = ProgressBar(5)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.step("b c d")

    message = caplog.messages[0]

    # Assert
    assert starts_with_green(message), f"Message '{message}' was not green."
    assert ends_with_color_reset(message), f"Message '{message}' did not end with a color reset."

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#    ]: b c d" == message


def test_progress_newline(caplog):
    # Arrange
    progressbar = ProgressBar(4)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.progress("a b c", newline=True)

    message = caplog.messages[0]

    # Assert
    assert starts_with_light_blue(message), f"Message '{message}' was not light blue."
    assert ends_with_color_reset(message), f"Message '{message}' did not end with a color reset."

    # Act
    message = get_original_message(message)

    # Assert
    assert "[+   ]: a b c" == message


def test_step_no_newline(caplog):
    # Arrange
    progressbar = ProgressBar(5)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.step("b c d", newline=False)

    message = caplog.messages[0]

    # Assert
    assert starts_with_green(message), f"Message '{message}' was not green."
    assert ends_with_color_reset_and_carriage_return(message), (f"Message '{message}' did not end with a "
                                                                f"color reset and carriage return.")

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#    ]: b c d" == message


def test_step_step(caplog):
    # Arrange
    progressbar = ProgressBar(5)
    progressbar.step("")

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.step("")

    message = caplog.messages[0]

    # Assert
    assert starts_with_green(message), f"Message '{message}' was not green."
    assert ends_with_color_reset(message), f"Message '{message}' did not end with a color reset."

    # Act
    message = get_original_message(message)

    # Assert
    assert "[##   ]: " == message


# noinspection DuplicatedCode
def test_step_progress(caplog):
    # Arrange
    progressbar = ProgressBar(5)
    progressbar.step("")

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.progress("")

    message = caplog.messages[0]

    # Assert
    assert starts_with_light_blue(message), f"Message '{message}' was not green."
    assert ends_with_color_reset_and_carriage_return(message), (f"Message '{message}' did not end with a "
                                                                f"color reset and carriage return.")

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#+   ]: " == message


# noinspection DuplicatedCode
def test_progress_progress(caplog):
    # Arrange
    progressbar = ProgressBar(5)
    progressbar.progress("")

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.progress("")

    message = caplog.messages[0]

    # Assert
    assert starts_with_light_blue(message), f"Message '{message}' was not green."
    assert ends_with_color_reset_and_carriage_return(message), (f"Message '{message}' did not end with a "
                                                                f"color reset and carriage return.")

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#+   ]: " == message


def test_progress_step(caplog):
    # Arrange
    progressbar = ProgressBar(5)
    progressbar.progress("")

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.step("")

    message = caplog.messages[0]

    # Assert
    assert starts_with_green(message), f"Message '{message}' was not green."
    assert ends_with_color_reset(message), f"Message '{message}' did not end with a color reset and carriage return."

    # Act
    message = get_original_message(message)

    # Assert
    assert "[#    ]: " == message


def test_padding_length(caplog):
    # Arrange
    progressbar = ProgressBar(9)
    progressbar.progress("qwerty" * 3)
    expected_progress = "[#+       ]: "

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.progress("")

    message = get_original_message(caplog.messages[0])
    expected_output = expected_progress + " " * len("qwerty") * 3

    # Assert
    assert expected_output == message


def test_short_bar_step(caplog):
    # Arrange
    progressbar = ProgressBar(1)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.step("")

    message = get_original_message(caplog.messages[0])

    # Assert
    assert "[#]: " == message


def test_short_bar_progress(caplog):
    # Arrange
    progressbar = ProgressBar(1)

    # Act
    with caplog.at_level(logging.INFO):
        progressbar.progress("")

    message = get_original_message(caplog.messages[0])

    # Assert
    assert "[+]: " == message


def test_short_bar_progress_step(caplog):
    # Arrange
    progressbar = ProgressBar(1)
    progressbar.progress("")
    # Act
    with caplog.at_level(logging.INFO):
        progressbar.step("")

    message = get_original_message(caplog.messages[0])

    # Assert
    assert "[#]: " == message


def test_progress_overflow(caplog):
    # Arrange
    progressbar = ProgressBar(1)
    progressbar.step("")

    # Assert
    with pytest.raises(OverflowError):
        progressbar.step("")
