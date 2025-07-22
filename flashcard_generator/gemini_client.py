"""
Google Gemini API client for generating word pairs and translations.
"""

import time
import json
import logging
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .models import WordPair
from .exceptions import GeminiAPIError, AuthenticationError, RateLimitError, NetworkError

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini 2.5 API."""
    
    def __init__(self, api_key: str):
        """Initialize the Gemini client with API key."""
        self.api_key = api_key
        self._client = None
        self._model = None
        self.max_retries = 3
        self.base_delay = 1.0
    
    def authenticate(self) -> bool:
        """Authenticate with the Gemini API with enhanced error handling."""
        try:
            genai.configure(api_key=self.api_key)
            

            self._model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
            
            # Test the connection with a simple request
            test_response = self._model.generate_content("Hello")
            if test_response and test_response.text:
                logger.info("Successfully authenticated with Gemini API")
                return True
            else:
                logger.error("Authentication test failed - no response received")
                raise AuthenticationError(
                    "Authentication test failed - no response received",
                    api_name="Gemini",
                    details={"api_key_length": len(self.api_key)}
                )
                
        except AuthenticationError:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
                raise AuthenticationError(
                    f"Invalid API key or authentication failed: {e}",
                    api_name="Gemini",
                    details={"original_error": str(e)}
                )
            elif "network" in error_msg or "connection" in error_msg:
                raise NetworkError(
                    f"Network error during authentication: {e}",
                    details={"original_error": str(e)}
                )
            else:
                logger.error(f"Failed to authenticate with Gemini API: {e}")
                raise GeminiAPIError(
                    f"Authentication failed: {e}",
                    details={"original_error": str(e)}
                )
    
    def generate_word_pairs(self, topic: str, count: int, context: Optional[str] = None) -> List[WordPair]:
        """Generate English-Chinese word pairs for a given topic."""
        # Input validation
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")
        if count <= 0:
            raise ValueError("Count must be greater than 0")
        if count > 50:
            raise ValueError("Count cannot exceed 50 to avoid API limits")
            
        if not self._model:
            if not self.authenticate():
                raise RuntimeError("Failed to authenticate with Gemini API")
        
        prompt = self._create_word_generation_prompt(topic.strip(), count, context)
        
        for attempt in range(self.max_retries):
            try:
                response = self._make_api_call(prompt)
                word_pairs = self._parse_word_pairs_response(response)
                
                if word_pairs:
                    logger.info(f"Successfully generated {len(word_pairs)} word pairs for topic: {topic}")
                    return word_pairs[:count]  # Ensure we don't exceed requested count
                else:
                    logger.warning(f"No valid word pairs generated on attempt {attempt + 1}")
                    if attempt == self.max_retries - 1:
                        raise RuntimeError(f"Failed to generate valid word pairs for topic: {topic}")
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for topic: {topic}")
                    raise RuntimeError(f"Failed to generate word pairs after {self.max_retries} attempts")
        
        return []
    
    def translate_to_chinese(self, english_word: str) -> str:
        """Translate an English word to Chinese."""
        # Input validation
        if not english_word or not english_word.strip():
            raise ValueError("English word cannot be empty")
            
        if not self._model:
            if not self.authenticate():
                raise RuntimeError("Failed to authenticate with Gemini API")
        
        clean_word = english_word.strip()
        prompt = f"""
        Translate the English word "{clean_word}" to Chinese (Simplified).
        
        Provide only the Chinese translation, no additional text or explanation.
        The translation should be the most common and appropriate Chinese equivalent.
        
        English word: {clean_word}
        Chinese translation:
        """
        
        for attempt in range(self.max_retries):
            try:
                response = self._make_api_call(prompt)
                chinese_translation = response.strip()
                
                if chinese_translation and len(chinese_translation) > 0:
                    logger.info(f"Successfully translated '{english_word}' to '{chinese_translation}'")
                    return chinese_translation
                else:
                    logger.warning(f"Empty translation received on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise RuntimeError(f"Failed to translate '{english_word}' after {self.max_retries} attempts")
        
        raise RuntimeError(f"Failed to translate '{english_word}'")
    
    def _create_word_generation_prompt(self, topic: str, count: int, context: Optional[str] = None) -> str:
        """Create a structured prompt for word generation."""
        context_instruction = ""
        if context:
            context_instruction = f"\n        Additional Context: {context}\n        Please consider this context when selecting words and creating sentences."
        
        return f"""
        Generate {count} English words related to the topic "{topic}" along with their Chinese (Simplified) translations, pinyin pronunciation, and example sentences.{context_instruction}
        
        Requirements:
        1. Words should be commonly used and appropriate for language learning
        2. Each word should be a single word or simple phrase (no complex sentences)
        3. Chinese translations should use Simplified Chinese characters
        4. Provide accurate pinyin pronunciation with tone numbers (e.g., "mao1" for 猫)
        5. Provide the most common and accurate translation for each word
        6. Include example sentences in four formats: English, Chinese, Pinyin, and a fill-in-the-blank test
        7. Words should be suitable for flashcard learning
        
        Format your response as a JSON array with this exact structure:
        [
            {{"english": "word1", "chinese": "中文1", "pinyin": "pinyin1", "sentence": "Example sentence using word1.<br>使用中文1的简单中文句子。<br>Pinyin version of the Chinese sentence.<br>我喜欢吃____。<br>Wǒ xǐhuan chī ____.""}},
            {{"english": "word2", "chinese": "中文2", "pinyin": "pinyin2", "sentence": "Example sentence using word2.<br>使用中文2的简单中文句子。<br>Pinyin version of the Chinese sentence.<br>今天天气很____。<br>Jīntiān tiānqì hěn ____.""}},
            ...
        ]
        
        Topic: {topic}
        Number of words: {count}
        
        JSON Response:
        """
    
    def _make_api_call(self, prompt: str) -> str:
        """Make an API call to Gemini with error handling."""
        try:
            response = self._model.generate_content(prompt)
            
            if not response or not response.text:
                raise RuntimeError("Empty response from Gemini API")
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
    
    def _parse_word_pairs_response(self, response: str) -> List[WordPair]:
        """Parse the JSON response from Gemini into WordPair objects."""
        try:
            # Clean up the response - remove any markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            word_data = json.loads(cleaned_response)
            
            if not isinstance(word_data, list):
                logger.error("Response is not a JSON array")
                return []
            
            word_pairs = []
            for item in word_data:
                try:
                    if isinstance(item, dict) and 'english' in item and 'chinese' in item and 'pinyin' in item:
                        english = item['english'].strip()
                        chinese = item['chinese'].strip()
                        pinyin = item['pinyin'].strip()
                        sentence = item.get('sentence', '').strip()  # Optional sentence field
                        
                        if english and chinese and pinyin:
                            word_pair = WordPair(
                                english=english, 
                                chinese=chinese, 
                                pinyin=pinyin,
                                sentence=sentence if sentence else None
                            )
                            word_pairs.append(word_pair)
                        else:
                            logger.warning(f"Skipping empty word pair: {item}")
                    else:
                        logger.warning(f"Invalid word pair format: {item}")
                        
                except Exception as e:
                    logger.warning(f"Error creating WordPair from {item}: {e}")
                    continue
            
            return word_pairs
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {response}")
            return []
        except Exception as e:
            logger.error(f"Error parsing word pairs response: {e}")
            return []