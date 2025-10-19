"""
Factory for creating appropriate cleaners based on domain
"""
from typing import Type, Dict
from .base_cleaner import BaseCleaner
from .daa_cleaner import DaaCleaner
from .uit_cleaner import UitCleaner


class CleanerFactory:
    """Factory to create appropriate cleaner for different domains"""

    # This dictionary maps a domain string to a cleaner CLASS (a blueprint).
    _cleaners: Dict[str, Type[BaseCleaner]] = {
        'daa.uit.edu.vn': DaaCleaner,
        #'uit.edu.vn': UitCleaner,
    }

    @classmethod
    def get_cleaner(cls, domain: str) -> BaseCleaner:
        """
        Get an INSTANCE of the appropriate cleaner based on a domain name.

        Args:
            domain: The domain name (e.g., 'daa.uit.edu.vn').

        Raises:
            ValueError: If no cleaner is found for the given domain.
        """
        cleaner_class = cls._cleaners.get(domain)

        if cleaner_class:
            # Return an instance of the class.
            return cleaner_class()
        else:
            raise ValueError(f"No cleaner registered for domain: '{domain}'")

    @classmethod
    def register_cleaner(cls, domain: str, cleaner_class: Type[BaseCleaner]):
        """
        Register a new cleaner CLASS for a domain.

        Args:
            domain: The domain name to associate with the cleaner.
            cleaner_class: The cleaner class to register (must be a subclass of BaseCleaner).
        """
        if not issubclass(cleaner_class, BaseCleaner):
            raise TypeError("cleaner_class must be a subclass of BaseCleaner")
        cls._cleaners[domain] = cleaner_class
