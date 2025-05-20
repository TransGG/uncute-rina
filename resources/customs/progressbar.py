from resources.utils.utils import debug


class ProgressBar:
    def __init__(
            self,
            max_steps: int,
            *,
            fill_char: str = '#',
            progress_char: str = '+',
            empty_char: str = ' '
    ):
        self._max_steps = max_steps
        self._step = 0
        self._fill_char = fill_char
        self._progress_char = progress_char
        self._empty_char = empty_char
        if not (len(fill_char) == len(progress_char) == len(empty_char)):
            raise ValueError("Progress characters must have the same length!")
        self._just_progressed = False
        self._previous_message_length = 0

    def _get_progess_bar(self, *, busy) -> str:
        """
        A helper function to construct a progress bar based on
        current progress.

        :param busy: Whether to add a :py:attr:`_progress_char` in
         the bar.
        :return: A progress bar string of the current progress, with
         opening and closing parentheses: "[   ]:".
        """
        out = "["
        out += self._fill_char * self._step
        if busy:
            out += self._progress_char
        # [###+ = 5 chars. Max step may be 4. Pad 0 characters. [###+]:
        pad_chars = self._max_steps - len(out) + 1
        if pad_chars < 0:
            raise OverflowError("Progress exceeded size of progress bar!")
        out += self._empty_char * pad_chars
        out += "]: "
        return out

    def _get_line_clear_padding(self, string) -> str:
        """
        A helper function to get the amount of spaces necessary to
        overwrite the previous progress message.

        :param string: The text of the upcoming progress message.
        :return: A string with spaces to overwrite the previous
         progress message.
        """
        length = len(string)
        length = max(self._previous_message_length - length, 0)
        return " " * length

    def progress(self, text, *, newline=False) -> None:
        """
        Print a debug log, incrementing the progress bar with
        the :py:attr:`_progress_char`.

        :param text: The text to place after the progress bar.
        :param newline: Whether to place a newline after the progress
         bar, or reset the caret to overwrite this line with the next
         progress bar step.
        """
        end = '\n' if newline else '\r'
        if self._just_progressed:
            # to prevent two progress chars in a row: "[#++ ]:"
            self._step += 1
        progress_bar = self._get_progess_bar(busy=True)
        padding = self._get_line_clear_padding(text)
        debug(progress_bar + text + padding, color="light_blue", end=end)
        self._previous_message_length = len(text) if not newline else 0
        self._just_progressed = True

    def step(self, text, *, newline=True):
        """
        Print a debug log, incrementing the progress bar with
        the :py:attr:`_fill_char`.

        :param text: The text to place after the progress bar.
        :param newline: Whether to place a newline after the progress
         bar, or reset the caret to overwrite this line with the next
         progress bar step.
        """
        end = '\n' if newline else '\r'
        self._step += 1
        progress_bar = self._get_progess_bar(busy=False)
        padding = self._get_line_clear_padding(text)
        debug(progress_bar + text + padding, color="green", end=end)
        self._previous_message_length = len(text) if not newline else 0
        self._just_progressed = False
