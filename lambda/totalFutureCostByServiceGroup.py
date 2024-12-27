import boto3
from datetime import datetime, timedelta

# Initialize the Cost Explorer client
client = boto3.client('ce')

# Define the forecast parameters
start_date = datetime.today().date()
end_date = (start_date + timedelta(days=90)).strftime('%Y-%m-%d')  # Forecast for 3 months
start_date = start_date.strftime('%Y-%m-%d')

# Function to get a forecast for a specific service
def get_service_forecast(service):
    response = client.get_cost_forecast(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Metric='UNBLENDED_COST',  # Options: UNBLENDED_COST, AMORTIZED_COST
        Granularity='MONTHLY',  # Options: DAILY, MONTHLY
        PredictionIntervalLevel=95,  # Confidence interval level
        Filter={
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': [service]
            }
        }
    )
    return response['ForecastResultsByTime']

# Retrieve a list of services used in the account
services_response = client.get_dimension_values(
    TimePeriod={
        'Start': (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'End': datetime.today().strftime('%Y-%m-%d')
    },
    Dimension='SERVICE'
)

services = [item['Value'] for item in services_response['DimensionValues']]

# Loop through each service and get its forecast
print("Cost Forecast by Service:")
for service in services:
    forecasts = get_service_forecast(service)
    print(f"Service: {service}")
    for forecast in forecasts:
        print(f"  Time Period: {forecast['TimePeriod']}")
        print(f"  Predicted Cost: {forecast['MeanValue']} USD")
        print(f"  Confidence Interval: [{forecast['PredictionIntervalLowerBound']} - {forecast['PredictionIntervalUpperBound']}] USD")
    print("\n")
