import boto3
import os
import logging
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

def get_bedrock_client():
    """
    Creates and returns a boto3 client for Amazon Bedrock
    
    Returns:
        boto3.client: Configured Bedrock client
        
    Raises:
        NoCredentialsError: If AWS credentials are not found
        Exception: For other unexpected errors
    """
    try:
        region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Create a Bedrock client
        bedrock_client = boto3.client(
            service_name='bedrock',
            region_name=region
        )
        
        return bedrock_client
        
    except NoCredentialsError:
        logger.error("No AWS credentials found")
        raise
    except Exception as e:
        logger.error(f"Error creating Bedrock client: {str(e)}")
        raise
