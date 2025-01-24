import yaml
import boto3
import os
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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
        #print(response)
        return response
    except ClientError as e:
        print(
            f"Error fetching cost and usage for tag values {tag_values}: {e}")
        return None
    


start_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")
tag_key= "aws:cloudformation:logical-id"
tag_value= "CostReportLambda"
granularity= "DAILY"
metrics=["UnblendedCost"]
response = get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            tag_key=tag_key,
            tag_values=[tag_value],
            granularity=granularity,
            metrics=metrics
)

print(response)

total_cost = 0.0
for result in response["ResultsByTime"]:
    amount = float(result["Total"]["UnblendedCost"]["Amount"])
    total_cost += amount

print(f"Total Cost: ${total_cost:.7f} USD")

