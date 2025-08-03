from resources.utils import DebugColor
from resources.utils.utils import debug


class ProgressBar:
    def __init__(
            self,
            max_completes: int,
            *,
            complete_char: str = '#',
            begin_char: str = '+',
            empty_char: str = ' '
    ):
        self._max_completes = max_completes
        self._completions = 0
        self._complete_char = complete_char
        self._begin_char = begin_char
        self._empty_char = empty_char
        if not (len(complete_char) == len(begin_char) == len(empty_char)):
            raise ValueError("Progress characters must have the same length!")
        self._just_began = False
        self._previous_message_length = 0

    def _get_progess_bar(self, *, busy) -> str:
        """
        A helper function to construct a progress bar based on
        current progress.

        :param busy: Whether to add a :py:attr:`_begin_char` in
         the bar.
        :return: A progress bar string of the current progress, with
         opening and closing parentheses: "[   ]:".
        """
        out = "["
        out += self._complete_char * self._completions
        if busy:
            out += self._begin_char
        # [###+ = 5 chars. Max complete may be 4. Pad 0 characters. [###+]:
        pad_chars = self._max_completes - len(out) + 1
        if pad_chars < 0:
            raise OverflowError("Progress exceeded size of progress bar!")
        out += self._empty_char * pad_chars
        out += "]: "
        return out

    def _get_line_clear_padding(self, string) -> str:
        """
        A helper function to get the amount of spaces necessary to
        overwrite the previous 'begin' message.

        :param string: The text of the upcoming 'begin' message.
        :return: A string with spaces to overwrite the previous
         'begin' message.
        """
        length = len(string)
        length = max(self._previous_message_length - length, 0)
        return " " * length

    def begin(self, text, *, newline=False) -> None:
        """
        Print a debug log, incrementing the progress bar with
        the :py:attr:`_begin_char`.

        :param text: The text to place after the progress bar.
        :param newline: Whether to place a newline after the progress
         bar, or reset the caret to overwrite this line with the next
         progress bar completion.
        """
        end = '\n' if newline else '\r'
        if self._just_began:
            # to prevent 2x begin_char in a row: "[#++ ]:"
            self._completions += 1
        progress_bar = self._get_progess_bar(busy=True)
        padding = self._get_line_clear_padding(text)
        debug(progress_bar + text + padding, color=DebugColor.lightblue, end=end)
        self._previous_message_length = len(text) if not newline else 0
        self._just_began = True

    def complete(self, text, *, newline=True):
        """
        Print a debug log, incrementing the progress bar with
        the :py:attr:`_complete_char`.

        :param text: The text to place after the progress bar.
        :param newline: Whether to place a newline after the progress
         bar, or reset the caret to overwrite this line with the next
         progress bar completion.
        """
        end = '\n' if newline else '\r'
        self._completions += 1
        progress_bar = self._get_progess_bar(busy=False)
        padding = self._get_line_clear_padding(text)
        debug(progress_bar + text + padding, color=DebugColor.green, end=end)
        self._previous_message_length = len(text) if not newline else 0
        self._just_began = False
