# AWS Bedrock Setup Guide

This project now supports using Claude models through AWS Bedrock instead of the Anthropic API directly.

## Prerequisites

1. AWS Account with Bedrock access
2. AWS credentials configured
3. Access to the Claude Sonnet 4.5 model in Bedrock

## Configuration

### 1. Update your `api/.env` file

Add or update these variables:

```bash
# AWS Bedrock configuration
AWS_REGION=us-west-2  # or your preferred region
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# AWS Credentials (if not using AWS CLI default profile)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# AWS_SESSION_TOKEN=your_session_token  # if using temporary credentials

# GitHub MCP Server configuration (still needed)
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
GITHUB_HOST=github.sie.sony.com
SERVER_SCRIPT_PATH=/path/to/mcp-binaries/github-mcp-server
```

### 2. AWS Credentials

The application will use AWS credentials in this order:
1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM role (if running on EC2/ECS/Lambda)

## Available Bedrock Models

You can use any Claude model available in Bedrock. Update the `BEDROCK_MODEL_ID` in your `.env` file:

```bash
# Claude Sonnet 4.5 (Global)
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# Claude Sonnet 3.5 v2
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-3-5-v2:0

# Claude Sonnet 3.5 v1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# Claude Opus 3
BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0
```

## Benefits of Using Bedrock

- ✅ No need for Anthropic API key
- ✅ AWS-managed infrastructure
- ✅ Integrated with AWS IAM for security
- ✅ Pay-as-you-go pricing
- ✅ Access to latest Claude models
- ✅ Better compliance and governance

## Troubleshooting

### "Failed to call LLM via Bedrock"

1. **Check AWS credentials**: Run `aws sts get-caller-identity` to verify
2. **Check region**: Ensure the model is available in your region
3. **Check permissions**: Your IAM role/user needs `bedrock:InvokeModel` permission
4. **Check model ID**: Verify the model ID is correct and available in your account

### Permission Error

Add this policy to your IAM role/user:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

## Testing

Test your Bedrock connection:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, test Bedrock connection"}' \
  --no-buffer
```

You should see a response from Claude via Bedrock!

