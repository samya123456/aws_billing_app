import boto3
from botocore.exceptions import ClientError


def get_cost_and_usage(start_date, end_date, tag_key, tag_values, granularity='MONTHLY', metrics=None):
    """
    Fetch AWS cost and usage based on the provided parameters.

    Args:
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        tag_key (str): Tag key to filter on.
        tag_values (list): List of tag values to filter on.
        granularity (str): Granularity of the cost data ('DAILY' or 'MONTHLY').
        metrics (list): List of metrics to retrieve. Defaults to ['UnblendedCost'].

    Returns:
        dict: AWS Cost Explorer response for the given filters.
    """
    if metrics is None:
        metrics = ['UnblendedCost']

    client = boto3.client('ce')

    time_period = {
        'Start': start_date,
        'End': end_date
    }

    # Define the tag filter
    tag_filter = {
        'Tags': {
            'Key': tag_key,
            'Values': tag_values,
            'MatchOptions': ['EQUALS']
        }
    }

    try:
        response = client.get_cost_and_usage(
            TimePeriod=time_period,
            Granularity=granularity,
            Metrics=metrics,
            Filter=tag_filter
        )
        return response
    except ClientError as e:
        print(f"Error fetching cost and usage: {e}")
        return None


if __name__ == "__main__":
    # Parameters (Replace these with your actual values or read from a config file)
    START_DATE = '2024-12-01'  # Start date (YYYY-MM-DD)
    END_DATE = '2024-12-31'    # End date (YYYY-MM-DD)
    TAG_KEY = 'BusinessUnit'   # Tag key
    TAG_VALUES = ['persostack']  # Tag values as a list
    GRANULARITY = 'MONTHLY'    # Granularity ('DAILY' or 'MONTHLY')
    METRICS = ['UnblendedCost']  # Metrics to retrieve

    # Fetch cost and usage
    result = get_cost_and_usage(
        START_DATE, END_DATE, TAG_KEY, TAG_VALUES, GRANULARITY, METRICS)

    # Print the response
    if result:
        print("Cost and Usage Response:")
        for time_result in result.get('ResultsByTime', []):
            print(time_result)
