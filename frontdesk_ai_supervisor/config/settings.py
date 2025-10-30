import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration management for the Frontdesk AI Supervisor system.
    All settings loaded from environment variables.
    """

    # LiveKit Configuration
    LIVEKIT_URL = os.getenv('LIVEKIT_URL')
    LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
    LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # AWS Configuration (optional, for DynamoDB)
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    DYNAMODB_TABLE_PREFIX = os.getenv('DYNAMODB_TABLE_PREFIX', 'frontdesk_')

    # Request timeout settings
    HELP_REQUEST_TIMEOUT_HOURS = int(os.getenv('HELP_REQUEST_TIMEOUT_HOURS', 2))
    HELP_REQUEST_TIMEOUT_SECONDS = HELP_REQUEST_TIMEOUT_HOURS * 3600

    # Supervisor settings
    SUPERVISOR_PORT = int(os.getenv('SUPERVISOR_PORT', 5000))

    # Database settings
    LOCAL_DB_FILE = os.getenv('LOCAL_DB_FILE', 'frontdesk_local_db.json')

    @classmethod
    def validate(cls):
        """
        Validate that required configuration is present.
        Only validates if LiveKit is enabled.
        """
        if os.getenv('LIVEKIT', '0') == '1':
            required = [
                'LIVEKIT_URL',
                'LIVEKIT_API_KEY',
                'LIVEKIT_API_SECRET',
                'OPENAI_API_KEY'
            ]
            missing = [key for key in required if not getattr(cls, key)]
            if missing:
                raise ValueError(f"Missing required config for LiveKit: {', '.join(missing)}")

        return True

    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)"""
        print("\nCurrent Configuration:")
        print(f"  SUPERVISOR_PORT: {cls.SUPERVISOR_PORT}")
        print(f"  LOCAL_DB_FILE: {cls.LOCAL_DB_FILE}")
        print(f"  HELP_REQUEST_TIMEOUT_HOURS: {cls.HELP_REQUEST_TIMEOUT_HOURS}")
        print(f"  LIVEKIT_ENABLED: {os.getenv('LIVEKIT', '0') == '1'}")
        if os.getenv('LIVEKIT', '0') == '1':
            print(f"  LIVEKIT_URL: {cls.LIVEKIT_URL}")
            print(f"  LIVEKIT_API_KEY: {'***' if cls.LIVEKIT_API_KEY else 'Not set'}")
            print(f"  OPENAI_API_KEY: {'***' if cls.OPENAI_API_KEY else 'Not set'}")
        print()