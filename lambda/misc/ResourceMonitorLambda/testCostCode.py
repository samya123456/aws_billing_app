import boto3
from botocore.exceptions import ClientError

# Initialize the Cost Explorer client
client = boto3.client('ce')

# Define the time period for the cost query
time_period = {
    'Start': '2024-12-01',  # Start date (YYYY-MM-DD)
    'End': '2024-12-31'     # End date (YYYY-MM-DD)
}

# Define the tag filter
tag_filter = {
    'Tags': {
        'Key': 'BusinessUnit',  # Replace with your tag key
        'Values': ['persostack'],  # Replace with your tag value(s)
        'MatchOptions': [
            'EQUALS'
                    ]

    }
}

try:
    # Get cost and usage
    response = client.get_cost_and_usage(
        TimePeriod=time_period,
        Granularity='MONTHLY',  # Options: DAILY, MONTHLY
        Metrics=['UnblendedCost'],
        Filter=tag_filter
    )

    # Print the response
    print("Cost and Usage Response:")
    for result in response.get('ResultsByTime', []):
        print(result)
except ClientError as e:
    print(f"Error: {e}")
