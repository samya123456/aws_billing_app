import boto3
from datetime import datetime, timedelta


def get_aws_usage_cost(start_date, end_date, granularity='DAILY', group_by=None):
    """
    Retrieves AWS usage and cost details.
    :param start_date: Start date for the query (YYYY-MM-DD).
    :param end_date: End date for the query (YYYY-MM-DD).
    :param granularity: Granularity of the data ('DAILY' or 'MONTHLY').
    :param group_by: List of dictionaries for grouping (e.g., [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]).
    :return: Cost and usage details.
    """
    client = boto3.client('ce', region_name='us-east-1')  # Cost Explorer API is available in us-east-1

    # Define the request
    request = {
        'TimePeriod': {
            'Start': start_date,
            'End': end_date
        },
        'Granularity': granularity,
        'Metrics': ['UnblendedCost'],
    }
    if group_by:
        request['GroupBy'] = group_by

    # Get cost and usage data
    response = client.get_cost_and_usage(**request)

    return response

def display_usage_cost(response):
    """
    Displays the usage and cost details from the Cost Explorer API response.
    :param response: Response from Cost Explorer API.
    """
    print(f"{'Date':<12} {'Service':<30} {'Cost (USD)':<10}")
    print("=" * 50)

    for result in response['ResultsByTime']:
        date = result['TimePeriod']['Start']
        for group in result.get('Groups', []):
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            print(f"{date:<12} {service:<30} ${cost:<10.2f}")
        # if 'Total' in result['Metrics']:
        #     total_cost = float(result['Metrics']['UnblendedCost']['Amount'])
        #     print(f"{date:<12} {'TOTAL':<30} ${total_cost:<10.2f}")
        try:
            if 'Total' in result.get('Metrics', {}):
                unblended_cost = result['Metrics']['UnblendedCost']
                total_cost = float(unblended_cost['Amount'])
                print(f"{date:<12} {'TOTAL':<30} ${total_cost:<10.2f}")
        except (KeyError, TypeError, ValueError) as e:
            print(f"Error processing total cost for {date}: {e}")




if __name__ == "__main__":
    try:
        # Define the time period (e.g., last 7 days)
        end_date = datetime.utcnow().date().isoformat()
        start_date = (datetime.utcnow() - timedelta(days=7)).date().isoformat()

        # Get cost and usage data grouped by service
        response = get_aws_usage_cost(
            start_date=start_date,
            end_date=end_date,
            granularity='DAILY',
            group_by=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        # Display the results
        display_usage_cost(response)

    except Exception as e:
        print(f"Error: {e}")
