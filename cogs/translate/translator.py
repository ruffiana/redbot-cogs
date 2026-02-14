"""
Translation logic module for the Translation cog.

This module handles all translation-related operations:
- Translating text to target languages
- Detecting message language
- Error handling for translation API failures

No Discord imports allowed - this module is pure business logic.
"""

import asyncio
import logging
from typing import Optional
import googletrans
from googletrans.models import Translated

logger = logging.getLogger(__name__)


class TranslatorError(Exception):
    """Base exception for translation-related errors."""

    pass


class LanguageNotFoundError(TranslatorError):
    """Raised when a language code is not recognized."""

    pass


class TranslationAPIError(TranslatorError):
    """Raised when the translation API fails."""

    pass


class Translator:
    """
    Handle translation operations using Google Translate.

    This class provides methods for translating text and detecting languages.
    All operations are async-safe but delegate to Google Translate's synchronous
    API via asyncio.to_thread() to avoid blocking the event loop.

    Attributes:
        _translator: Internal googletrans.Translator instance
        _timeout: Maximum seconds to wait for a translation request
    """

    # All language codes and names from googletrans
    LANGUAGE_CODES = googletrans.LANGUAGES

    def __init__(self, timeout: int = 10):
        """
        Initialize the translator.

        Args:
            timeout: Maximum seconds to wait for API calls. Defaults to 10.
        """
        self._translator = googletrans.Translator()
        self._timeout = timeout

    @staticmethod
    def normalize_language(language: str) -> Optional[str]:
        """
        Normalize language input to a valid language code.

        Handles user-friendly language names (e.g., "english", "spanish")
        and converts them to ISO 639-1 codes. Special handling for Chinese
        variants (defaults to Simplified Chinese).

        Args:
            language: Language name or code to normalize.
                Examples: "english", "en", "spanish", "es", "chinese", "zh"

        Returns:
            Normalized language code (lowercase), or None if invalid.

        Examples:
            >>> Translator.normalize_language("english")
            'en'
            >>> Translator.normalize_language("spanish")
            'es'
            >>> Translator.normalize_language("chinese")
            'chinese (simplified)'
        """
        language_lower = language.lower().strip()

        # Try direct code lookup first (e.g., "en" → "english")
        if language_lower in googletrans.LANGUAGES:
            return language_lower

        # Try reverse lookup (e.g., "english" → "en")
        for code, name in googletrans.LANGUAGES.items():
            if name.lower() == language_lower:
                # Special case: normalize Chinese variants
                if "chinese" in name.lower():
                    return "chinese (simplified)"
                return code

        # Partial match for Chinese variations
        if "chinese" in language_lower or language_lower in ("zh", "ch"):
            return "chinese (simplified)"

        return None

    async def translate(
        self, text: str, target_language: str, source_language: str = "auto"
    ) -> str:
        """
        Translate text to target language.

        Delegates to Google Translate API via asyncio.to_thread() to avoid
        blocking the event loop. Includes timeout protection.

        Args:
            text: Text to translate (can be empty, will return empty string)
            target_language: Target language code (e.g., "en", "es", "french")
            source_language: Source language code. Defaults to "auto" for detection.

        Returns:
            Translated text, or empty string if text is empty.

        Raises:
            LanguageNotFoundError: If target language is not recognized
            TranslationAPIError: If translation API call fails
            asyncio.TimeoutError: If translation exceeds timeout

        Examples:
            >>> result = await translator.translate("Hola", "english")
            >>> print(result)
            'Hello'

            >>> result = await translator.translate("", "english")
            >>> print(result)
            ''
        """
        if not text or not text.strip():
            return ""

        # Normalize target language
        target_language = self.normalize_language(target_language)
        if not target_language:
            raise LanguageNotFoundError(
                f"Language '{target_language}' is not recognized."
            )

        try:
            # Run translation in thread pool to avoid blocking event loop
            result: Translated = await asyncio.wait_for(
                asyncio.to_thread(
                    self._translator.translate, text, target_language, source_language
                ),
                timeout=self._timeout,
            )
            return result.text
        except asyncio.TimeoutError:
            logger.warning(
                f"Translation timeout after {self._timeout}s for language {target_language}"
            )
            raise
        except Exception as e:
            logger.error(f"Translation API error: {e}", exc_info=True)
            raise TranslationAPIError(str(e)) from e

    async def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the language of given text.

        Uses Google Translate's language detection. Returns the detected
        language code and confidence score.

        Args:
            text: Text to detect language for.

        Returns:
            Dictionary with detected language info:
                {
                    'code': 'es',
                    'name': 'spanish',
                    'confidence': 0.95
                }
            Returns None if detection fails or text is empty.

        Raises:
            TranslationAPIError: If detection API call fails

        Examples:
            >>> result = await translator.detect_language("Hola mundo")
            >>> print(result['code'])
            'es'
            >>> print(result['name'])
            'spanish'
        """
        if not text or not text.strip():
            return None

        try:
            result = await asyncio.to_thread(self._translator.detect, text)
            return {
                "code": result.lang,
                "name": self.LANGUAGE_CODES.get(result.lang, result.lang),
                "confidence": getattr(result, "confidence", 1.0),
            }
        except Exception as e:
            logger.error(f"Language detection error: {e}", exc_info=True)
            raise TranslationAPIError(str(e)) from e

    def get_available_languages(self) -> dict[str, str]:
        """
        Get all available language codes and their names.

        Returns:
            Dictionary mapping language codes to language names.
            Example: {'en': 'english', 'es': 'spanish', ...}
        """
        return dict(self.LANGUAGE_CODES)
