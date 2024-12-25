# Lambda Function Code
import boto3
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize clients
ce_client = boto3.client('ce')
ses_client = boto3.client('ses')

# Environment variables
APP_NAME = os.getenv('APP_NAME', 'DefaultApp')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'DefaultEnv')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')


def get_resources_by_tag(tag_key, tag_value):
    resource_client = boto3.client('resourcegroupstaggingapi')
    response = resource_client.get_resources(
        TagFilters=[{'Key': tag_key, 'Values': [tag_value]}]
    )
    return response.get('ResourceTagMappingList', [])


def get_cost_for_resource(resource_arn):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)

    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_time.strftime('%Y-%m-%d'),
            'End': end_time.strftime('%Y-%m-%d')
        },
        Granularity='DAILY',
        Metrics=['BlendedCost'],
        Filter={
            'Dimensions': {
                'Key': 'RESOURCE_ARN',
                'Values': [resource_arn]
            }
        }
    )
    return response['ResultsByTime'][0]['Total']['BlendedCost']['Amount']


def send_email(subject, body):
    try:
        ses_client.send_email(
            Source=EMAIL_RECIPIENT,
            Destination={
                'ToAddresses': [EMAIL_RECIPIENT]
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Text': {
                        'Data': body
                    }
                }
            }
        )
    except ClientError as e:
        print(f"Error sending email: {e}")


def lambda_handler(event, context):
    tag_key = event.get('tagKey', 'Environment')
    tag_value = event.get('tagValue', ENVIRONMENT)

    resources = get_resources_by_tag(tag_key, tag_value)
    total_cost = 0
    detail_data = []
    for resource in resources:
        arn = resource['ResourceARN']
        cost = get_cost_for_resource(arn)
        detail_data.append(arn, cost)
        total_cost += float(cost)

    #writting data to datafram
    df = pd.DataFrame(detail_data,columns=["Resource ARN", "Cost"])

    email_subject = f"{APP_NAME} Cost Report for {ENVIRONMENT}"
    email_body = f"Total 24-hour cost for {ENVIRONMENT}: ${total_cost:.2f}"

    send_email(email_subject, email_body)