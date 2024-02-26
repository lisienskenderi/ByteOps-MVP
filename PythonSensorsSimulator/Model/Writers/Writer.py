from abc import ABC, abstractmethod
from ..Simulators.Misurazione import Misurazione

#Pattern Strategy
class Writer(ABC):

    @abstractmethod
    def write(self, to_write: Misurazione) -> None:
        pass
