import boto3
from datetime import datetime, timedelta


def get_cost_forecast(client, start_date, end_date, service, metric, granularity, prediction_interval=95):
    """
    Fetch the cost forecast for a specific AWS service.

    Args:
        client (boto3.client): The initialized boto3 Cost Explorer client.
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        service (str): AWS service name for the forecast.
        metric (str): Metric type ('UNBLENDED_COST' or 'AMORTIZED_COST').
        granularity (str): Granularity of the forecast ('DAILY' or 'MONTHLY').
        prediction_interval (int): Confidence interval level for the forecast.

    Returns:
        list: Forecast results for the specified service.
    """
    response = client.get_cost_forecast(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Metric=metric,
        Granularity=granularity,
        PredictionIntervalLevel=prediction_interval,
        Filter={
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': [service]
            }
        }
    )
    return response.get('ForecastResultsByTime', [])


def get_services(client, time_period):
    """
    Retrieve a list of services used in the account.

    Args:
        client (boto3.client): The initialized boto3 Cost Explorer client.
        time_period (dict): Time period for retrieving service dimensions.

    Returns:
        list: List of service names used in the account.
    """
    response = client.get_dimension_values(
        TimePeriod=time_period,
        Dimension='SERVICE'
    )
    return [item['Value'] for item in response.get('DimensionValues', [])]


def display_cost_forecast_by_service(client, start_date, end_date, lookback_period, metric, granularity):
    """
    Display the cost forecast for each AWS service.

    Args:
        client (boto3.client): The initialized boto3 Cost Explorer client.
        start_date (str): Start date for the forecast in YYYY-MM-DD format.
        end_date (str): End date for the forecast in YYYY-MM-DD format.
        lookback_period (dict): Time period for fetching the list of services.
        metric (str): Metric type ('UNBLENDED_COST' or 'AMORTIZED_COST').
        granularity (str): Granularity of the forecast ('DAILY' or 'MONTHLY').
    """
    # Fetch services used in the account
    services = get_services(client, lookback_period)

    # Display cost forecast by service
    print("Cost Forecast by Service:")
    for service in services:
        forecasts = get_cost_forecast(
            client, start_date, end_date, service, metric, granularity)
        print(f"Service: {service}")
        for forecast in forecasts:
            time_period = forecast.get('TimePeriod', {})
            print(
                f"  Time Period: {time_period.get('Start')} to {time_period.get('End')}")
            print(f"  Predicted Cost: {forecast.get('MeanValue')} USD")
            print(
                f"  Confidence Interval: [{forecast.get('PredictionIntervalLowerBound')} - {forecast.get('PredictionIntervalUpperBound')}] USD")
        print("\n")


if __name__ == "__main__":
    days = 90
    look_back_days = 30
    client = boto3.client('ce')
    START_DATE = datetime.today().strftime('%Y-%m-%d')  # Current date
    END_DATE = (datetime.today() + timedelta(days=days)
                ).strftime('%Y-%m-%d')  # Forecast for 3 months
    LOOKBACK_START_DATE = (
        datetime.today() - timedelta(days=look_back_days)).strftime('%Y-%m-%d')
    LOOKBACK_END_DATE = datetime.today().strftime('%Y-%m-%d')

    lookback_period = {
        'Start': LOOKBACK_START_DATE,
        'End': LOOKBACK_END_DATE
    }

    # Parameters for cost forecast
    METRIC = 'AMORTIZED_COST'  # Options: 'UNBLENDED_COST', 'AMORTIZED_COST'
    GRANULARITY = 'DAILY'  # Options: 'DAILY', 'MONTHLY'

    # Call the method to display the forecast
    display_cost_forecast_by_service(
        client, START_DATE, END_DATE, lookback_period, METRIC, GRANULARITY)
