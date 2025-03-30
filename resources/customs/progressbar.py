from resources.utils.utils import debug


class ProgressBar:
    def __init__(self, max_steps: int, *, fill_char='#', progress_char='+', empty_char=' '):
        self._max_steps = max_steps
        self._step = 0
        self._fill_char = fill_char
        self._progress_char = progress_char
        self._empty_char = empty_char
        if not (len(fill_char) == len(progress_char) == len(empty_char)):
            raise ValueError(f"Progress characters must have the same length!")
        self._just_progressed = False
        self._previous_message_length = 0

    def _get_progess_bar(self, *, progressing) -> str:
        out = "["
        out += self._fill_char * self._step
        if progressing:
            out += "+"
        # [###+ = 5 chars. Max step may be 4. Pad 0 characters. [###+]:
        pad_chars = self._max_steps - len(out)
        out += " "*pad_chars

        out += "]: "
        return out

    def _get_line_clear_padding(self, string) -> str:
        length = len(string)
        length = max(self._previous_message_length - length, 0)
        return " " * length

    def progress(self, text, *, newline=False):
        end = '\n' if newline else '\r'
        if self._just_progressed:  # to prevent two progress chars in a row: "[##++  ]:"
            self._step += 1
        progress_bar = self._get_progess_bar(progressing=True)
        padding = self._get_line_clear_padding(text)
        debug(progress_bar + text + padding, color="light_blue", end=end)
        self._previous_message_length = len(text)
        self._just_progressed = True

    def step(self, text, *, newline=True):
        end = '\n' if newline else '\r'
        self._step += 1
        progress_bar = self._get_progess_bar(progressing=False)
        padding = self._get_line_clear_padding(text)
        debug(progress_bar + text + padding, color="green", end=end)
        self._previous_message_length = len(text)
        self._just_progressed = False
