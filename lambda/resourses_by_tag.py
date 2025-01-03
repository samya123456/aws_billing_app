import boto3
from datetime import datetime, timedelta
ce_client = boto3.client('ce')
ses_client = boto3.client('ses')


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


if __name__ == "__main__":
    tag_key = "BusinessUnit"
    tag_value = "persostack123"
    resources = get_resources_by_tag(tag_key, tag_value)
    total_cost = 0
    detail_data = []
    for resource in resources:
        arn = resource['ResourceARN']
        print("arns = ", arn)
        cost = get_cost_for_resource(arn)
        detail_data.append(arn, cost)
        total_cost += float(cost)
