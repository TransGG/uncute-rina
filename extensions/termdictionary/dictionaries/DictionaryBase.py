from abc import abstractmethod

import aiohttp
import discord

from resources.customs import Bot


class DictionaryBase:
    """
    Base class for dictionary sources to handle making and sending responses.

    Provides base functionality for dictionary sources. Subclasses must
    implement methods to construct and send responses.

    :ivar has_response: Indicates whether a response has been
     constructed.
    :ivar character_overflow: Indicates whether the constructed response
     exceeds Discord's character limit.
    """
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self.has_response = False
        self._character_overflow = False

    @abstractmethod
    async def get_autocomplete(self, current: str) -> set[str]:
        """Get a list of autocomplete terms based on the current input.

        :param current: The partial term input by the user for which
         autocomplete suggestions should be generated.
        :return: A set of possible autocomplete suggestions.
        """
        pass

    @abstractmethod
    async def construct_response(self, term: str) -> None:
        """Construct a response for the given dictionary term.

        :param term: The dictionary term to construct a response for.
        :return: ``None``. The response is stored internally.
         Use :py:attr:has_response: to see if a response could be
         constructed. If so, run :py:meth:`send_response`.
        """
        pass

    @abstractmethod
    async def send_response(
            self,
            itx: discord.Interaction[Bot],
            public: bool
    ) -> None:
        """Send the dictionary response to the user.

        :param itx: The interaction to respond to.
        :param public: Whether the response should be sent publicly.
        """
        pass

    @abstractmethod
    async def handle_no_response(
            self,
            itx: discord.Interaction[Bot],
            term: str
    ) -> None:
        """
        Send an error message that no valid response was found.

        .. note::

            This function has no checks, so you should first check
            if :py:attr:has_response: is ``True``.

        :param term:
        :param itx: The interaction to respond to.
        :return: None.
        """
        pass
