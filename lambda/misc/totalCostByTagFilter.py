import yaml
import boto3
from botocore.exceptions import ClientError
from datetime import datetime


def get_cost_and_usage(start_date, end_date, tag_key, tag_values, granularity='MONTHLY', metrics=None):
    """
    Fetch AWS cost and usage based on the provided parameters.
    """
    if metrics is None:
        metrics = ['UnblendedCost']

    client = boto3.client('ce')

    time_period = {
        'Start': start_date,
        'End': end_date
    }

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
        print(
            f"Error fetching cost and usage for tag values {tag_values}: {e}")
        return None


def process_cost_usage_from_yaml(yaml_file):
    with open(yaml_file, 'r') as file:
        config = yaml.safe_load(file)

    # Extract data for each tag setting
    tag_settings = config.get("aws_cost_usage", {}).get("tag_settings", [])
    for setting in tag_settings:
        tag_key = setting.get("tag_key")
        tag_value = setting.get("tag_value")
        granularity = setting.get("granularity", "MONTHLY")
        metrics = setting.get("metrics", ["UnblendedCost"])
        time_period = setting.get("time_period", {})
        start_date = time_period.get("start_date")
        end_date = time_period.get("end_date")

        print(f"Calling cost and usage for tag value: {tag_value}")
        result = get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            tag_key=tag_key,
            tag_values=[tag_value],
            granularity=granularity,
            metrics=metrics
        )

        # Print the result
        if result:
            print(f"Cost and Usage Response for {tag_value}:")
            for time_result in result.get('ResultsByTime', []):
                print(time_result)
        else:
            print(f"No data found for tag value: {tag_value}")
        print("="*40)


if __name__ == "__main__":
    yaml_file = "config.yaml"  # Replace with your YAML file name
    process_cost_usage_from_yaml(yaml_file)
