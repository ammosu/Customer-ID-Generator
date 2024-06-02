from abc import ABC, abstractmethod
import pandas as pd

class DataAccess(ABC):

    @abstractmethod
    def file_exists(self) -> bool:
        pass

    @abstractmethod
    def save(self, data: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def load(self) -> pd.DataFrame:
        pass
