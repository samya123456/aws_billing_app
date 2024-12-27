import boto3
from datetime import datetime, timedelta

def get_cost_by_service_with_tag(start_date, end_date, tag_key, tag_value, granularity='DAILY'):
    """
    Retrieves AWS costs grouped by service for resources matching a specific tag.
    :param start_date: Start date for the query (YYYY-MM-DD).
    :param end_date: End date for the query (YYYY-MM-DD).
    :param tag_key: Tag key used to identify resources.
    :param tag_value: Tag value for the specific resource.
    :param granularity: Granularity of the data ('DAILY' or 'MONTHLY').
    :return: Cost grouped by service for the specified tag.
    """
    client = boto3.client('ce', region_name='us-east-1')  # Cost Explorer API is only available in us-east-1

    # Build filter for the tag
    tag_filter = {
        'Tags': {
            'Key': tag_key,
            'Values': [tag_value],
            'MatchOptions': ['EQUALS']
        }
    }

    # Query Cost Explorer
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity=granularity,
        Metrics=['UnblendedCost'],
        GroupBy=[
            {'Type': 'DIMENSION', 'Key': 'SERVICE'}
        ],
        Filter=tag_filter
    )

    return response

def display_cost_by_service(response):
    """
    Displays cost grouped by service.
    :param response: Response from Cost Explorer API.
    """
#    print("DEBUG: Full API Response:")
#    print(response)  # Print the raw response for debugging

    print(f"{'Service':<40} {'Cost (USD)':<10}")
    print("=" * 50)

    total_cost = 0.0
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            print(f"{service:<40} ${cost:<10.2f}")
            total_cost += cost

    print("=" * 50)
    print(f"Total Cost: ${total_cost:.2f}")

if __name__ == "__main__":
    try:
        # Define time range (last 7 days)
        end_date = datetime.utcnow().date().isoformat()
        start_date = (datetime.utcnow() - timedelta(days=30)).date().isoformat()

        # Define tag filter details
        tag_key = "BusinessUnit"  # Replace with your tag key
        tag_value = "persostack123"  # Replace with your tag value

        # Get cost grouped by service
        response = get_cost_by_service_with_tag(
            start_date=start_date,
            end_date=end_date,
            tag_key=tag_key,
            tag_value=tag_value,
            granularity='DAILY'
        )

        # Display the cost details
        display_cost_by_service(response)

    except Exception as e:
        print(f"Error: {e}")