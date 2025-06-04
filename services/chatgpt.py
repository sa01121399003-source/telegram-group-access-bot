"""
ChatGPT API integration service
"""
import openai
from openai import OpenAI
from loguru import logger
from config import Config
from typing import Optional

class ChatGPTService:
    def __init__(self):
        # Check if API key is configured
        if not Config.CHATGPT_API_KEY:
            logger.warning("ChatGPT API key not configured")
            self.client = None
            self.assistant_id = None
            return
            
        try:
            # Initialize OpenAI client with explicit parameters to avoid warnings
            self.client = OpenAI(
                api_key=Config.CHATGPT_API_KEY,
                timeout=30.0,  # Set explicit timeout
                max_retries=2  # Set explicit retry count
            )
            self.assistant_id = Config.CHATGPT_ASSISTANT_ID
            logger.info("ChatGPT service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatGPT service: {e}")
            self.client = None
            self.assistant_id = None
    
    async def get_response_with_history(self, message: str, user_id: int, group_id: int) -> Optional[str]:
        """Get response from ChatGPT with conversation history"""
        if not self.client or not self.assistant_id:
            logger.warning("ChatGPT service not properly configured")
            return None
            
        try:
            # Import here to avoid circular import
            from database.queries import DatabaseQueries
            
            # Get recent conversation history
            history = await DatabaseQueries.get_conversation_history(user_id, group_id, limit=10)
            
            # Create a thread for the conversation
            thread = self.client.beta.threads.create()
            
            # Add conversation history to thread
            for entry in history:
                if entry['message_type'] == 'user' and entry['message_text']:
                    self.client.beta.threads.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content=entry['message_text']
                    )
                if entry['message_type'] == 'assistant' and entry['response_text']:
                    self.client.beta.threads.messages.create(
                        thread_id=thread.id,
                        role="assistant", 
                        content=entry['response_text']
                    )
            
            # Add the new user message
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Wait for the run to complete
            while run.status in ['queued', 'in_progress']:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                
                # Add a small delay to avoid overwhelming the API
                import asyncio
                await asyncio.sleep(1)
            
            if run.status == 'completed':
                # Get the assistant's response
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Get the latest assistant message
                for message_obj in messages.data:
                    if message_obj.role == 'assistant':
                        content = message_obj.content[0].text.value
                        
                        # Save this conversation to history
                        await DatabaseQueries.add_conversation_message(
                            user_id, group_id, message, 'user'
                        )
                        await DatabaseQueries.add_conversation_message(
                            user_id, group_id, message, 'assistant', content
                        )
                        
                        logger.info(f"ChatGPT response with history generated for user {user_id}")
                        return content
                        
            elif run.status == 'failed':
                logger.error(f"ChatGPT run failed: {run.last_error}")
                return None
            
            logger.warning(f"ChatGPT run ended with status: {run.status}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error in ChatGPT service with history: {e}")
            # Fallback to simple response
            return await self.get_simple_response(message, user_id)
    
    async def get_response(self, message: str, user_id: int) -> Optional[str]:
        """Get response from ChatGPT assistant"""
        if not self.client or not self.assistant_id:
            logger.warning("ChatGPT service not properly configured")
            return None
            
        try:
            # Create a thread for the conversation
            thread = self.client.beta.threads.create()
            
            # Add the user message to the thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Wait for the run to complete
            while run.status in ['queued', 'in_progress']:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                
                # Add a small delay to avoid overwhelming the API
                import asyncio
                await asyncio.sleep(1)
            
            if run.status == 'completed':
                # Get the assistant's response
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Get the latest assistant message
                for message_obj in messages.data:
                    if message_obj.role == 'assistant':
                        content = message_obj.content[0].text.value
                        logger.info(f"ChatGPT response generated for user {user_id}")
                        return content
                        
            elif run.status == 'failed':
                logger.error(f"ChatGPT run failed: {run.last_error}")
                return None
            
            logger.warning(f"ChatGPT run ended with status: {run.status}")
            return None
            
        except openai.RateLimitError:
            logger.warning("ChatGPT API rate limit exceeded")
            return None
        except openai.APIError as e:
            logger.error(f"ChatGPT API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in ChatGPT service: {e}")
            return None
    
    async def get_simple_response(self, message: str, user_id: int) -> Optional[str]:
        """Get a simple response using the chat completions API (fallback method)"""
        if not self.client:
            logger.warning("ChatGPT service not properly configured")
            return None
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            if response.choices:
                content = response.choices[0].message.content
                logger.info(f"ChatGPT simple response generated for user {user_id}")
                return content
            
            return None
            
        except openai.RateLimitError:
            logger.warning("ChatGPT API rate limit exceeded")
            return None
        except openai.APIError as e:
            logger.error(f"ChatGPT API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in ChatGPT simple service: {e}")
            return None

    async def test_connection(self) -> bool:
        """Test ChatGPT API connection"""
        if not self.client:
            return False
            
        try:
            # Simple test to verify API connectivity
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"ChatGPT API connection test failed: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if ChatGPT service is properly configured"""
        return bool(Config.CHATGPT_API_KEY and Config.CHATGPT_ASSISTANT_ID and self.client)

# Global ChatGPT service instance
chatgpt_service = ChatGPTService()