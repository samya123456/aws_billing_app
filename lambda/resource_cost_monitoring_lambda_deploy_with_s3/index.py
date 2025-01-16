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


def delete_stack(stack_name):
    """
    Delete a CloudFormation stack.
    """
    client = boto3.client('cloudformation')
    try:
        client.delete_stack(StackName=stack_name)
        print(f"Stack {stack_name} deletion initiated.")
        return True
    except ClientError as e:
        print(f"Error deleting stack {stack_name}: {e}")
        return False

def stack_exists(stack_name):
    cloudformation = boto3.client('cloudformation')
    try:
        # Describe the stack to check if it exists
        response = cloudformation.describe_stacks(StackName=stack_name)
        # If the stack exists, return True
        return True
    except ClientError as e:
        # If a "ValidationError" is raised, the stack does not exist
        if "does not exist" in str(e):
            return False
        else:
            # Re-raise the exception if it's not a "stack does not exist" error
            raise

def lambda_handler(event, context):
    """
    Lambda entry point.
    """
    s3_bucket= os.environ.get('S3_SOURCE_BUCKET')
    s3_key = os.environ.get('S3_FILE_NAME')
    s3 = boto3.client('s3')
    try:
        print(f"Bucket: {s3_bucket}, Key: {s3_key}")
        response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        yaml_content = response['Body'].read().decode('utf-8')
        config= yaml.safe_load(yaml_content)
    except FileNotFoundError:
        return {"error": "Configuration file not found"}

    results = []
    tag_settings = config.get("aws_cost_usage", {}).get("tag_settings", [])
    for setting in tag_settings:
        tag_key = setting.get("tag_key")
        tag_value = setting.get("tag_value")
        stack_name = setting.get("stack_name")
        if stack_exists(stack_name):
            print(f"The stack '{stack_name}' is present in source list and also exists in environment.")
        else:
            print(f"The stack '{stack_name}' is present in source list but does not exist in environment.")
            continue # Skip the current iteration when stack does not exist in environment
        granularity = setting.get("granularity", "MONTHLY")
        metrics = setting.get("metrics", ["UnblendedCost"])
        total_budget = setting.get("total_budget", 0)
        end_date = datetime.now().strftime("%Y-%m-%d")
        if granularity == "DAILY":
            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            print("Start Date = ", start_date)
            print("End Date = ", end_date)
        elif granularity == "MONTHLY":
            current_date = datetime.now()
            previous_month_date = current_date - relativedelta(months=1)
            start_date = previous_month_date.strftime("%Y-%m-%d") 
            print("Start Date = ", start_date)
            print("End Date = ", end_date)
        else:
            print("granularity value is neither daily nor monthly")
        print(tag_key)
        print(tag_value)
        print(stack_name)
        # Fetch cost and usage
        response = get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            tag_key=tag_key,
            tag_values=[tag_value],
            granularity=granularity,
            metrics=metrics
        )
        if response:

            # total_cost = sum(float(item['Total']['Amount'])
            #                  for item in response.get('ResultsByTime', []))
            
            total_cost = sum(float(item['Total']['Amount']) if 'Total' in item and 'Amount' in item['Total'] else 0


        for item in response.get('ResultsByTime', []))
            print("total cost =",total_cost)

            results.append({
                "tag_value": tag_value,
                "total_cost": total_cost,
                "total_budget": total_budget,
                "stack_name": stack_name,
                "status": "over_budget" if total_cost >= total_budget else "within_budget"
            })
            print("Debug Point1")
            # Delete stack if cost exceeds the budget
            if total_cost >= total_budget:
                print(
                    f"Total cost for {tag_value} exceeds the budget. Initiating stack deletion for {stack_name}.")
                delete_stack(stack_name)
                print("Debug Point2")
            else:
              results.append({
                "tag_value": tag_value,
                "error": "No cost data available"
            })
              
    print(results)
    return {"status": "success", "data": results}
