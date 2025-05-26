import yaml
import boto3
import os
from botocore.exceptions import ClientError
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_cost_and_usage(start_date, end_date, tag_key, tag_values, granularity='MONTHLY', metrics=None):
    if metrics is None:
        metrics = ['UnblendedCost']

    client = boto3.client('ce')
    time_period = {'Start': start_date, 'End': end_date}

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

        results = response.get('ResultsByTime', [])
        total_cost = sum(
            float(item.get('Total', {}).get('UnblendedCost', {}).get('Amount', 0.0))
            for item in results
        )

        print(f"🧾 Filtered cost for tag {tag_key}:{tag_values} = ${total_cost:.2f}")

        if total_cost == 0.0:
            print(" Filtered cost is $0 — checking total AWS cost without tag filters.")
            raw_response = client.get_cost_and_usage(
                TimePeriod=time_period,
                Granularity=granularity,
                Metrics=metrics
            )
            raw_total = sum(
                float(item.get('Total', {}).get('UnblendedCost', {}).get('Amount', 0.0))
                for item in raw_response.get('ResultsByTime', [])
            )
            print(f"📊 Total AWS Cost (Unfiltered) = ${raw_total:.2f}")

        return total_cost

    except ClientError as e:
        print(f"❌ Error fetching cost and usage for tag {tag_key}:{tag_values} - {e}")
        return 0.0

def delete_stack(stack_name):
    client = boto3.client('cloudformation')
    try:
        client.delete_stack(StackName=stack_name)
        print(f"🧨 Stack {stack_name} deletion initiated.")
        return True
    except ClientError as e:
        print(f"❌ Error deleting stack {stack_name}: {e}")
        return False

def stack_exists(stack_name):
    client = boto3.client('cloudformation')
    try:
        client.describe_stacks(StackName=stack_name)
        return True
    except ClientError as e:
        if "does not exist" in str(e):
            return False
        raise

def send_notification(subject, message):
    sns = boto3.client('sns')
    print("📧 Sending email notification...")
    sns.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Subject=subject,
        Message=message
    )

def lambda_handler(event, context):
    s3_bucket = os.environ.get('S3_SOURCE_BUCKET')
    s3_key = os.environ.get('S3_FILE_NAME')
    s3 = boto3.client('s3')

    try:
        print(f"📥 Reading config from S3 - Bucket: {s3_bucket}, Key: {s3_key}")
        response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        yaml_content = response['Body'].read().decode('utf-8')
        config = yaml.safe_load(yaml_content)
    except Exception as e:
        return {"error": f"❌ Failed to read configuration file: {e}"}

    results = []
    tag_settings = config.get("aws_cost_usage", {}).get("tag_settings", [])

    for setting in tag_settings:
        tag_key = setting.get("tag_key")
        tag_value = setting.get("tag_value")
        stack_name = setting.get("stack_name")
        total_budget = setting.get("total_budget", 0)
        granularity = setting.get("granularity", "MONTHLY")
        metrics = setting.get("metrics", ["UnblendedCost"])

        if not stack_exists(stack_name):
            print(f"⛔ Stack '{stack_name}' does not exist. Skipping.")
            results.append({
                "tag_key": tag_key,
                "tag_value": tag_value,
                "stack_name": stack_name,
                "error": "Stack does not exist"
            })
            continue

        today = datetime.utcnow().date()
        if granularity == "DAILY":
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
        elif granularity == "MONTHLY":
            previous_month = datetime.now() - relativedelta(months=1)
            start_date = previous_month.strftime("%Y-%m-%d")
        else:
            print(f" Invalid granularity: {granularity}. Skipping.")
            continue

        end_date = datetime.now().strftime("%Y-%m-%d")

        total_cost = get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            tag_key=tag_key,
            tag_values=[tag_value],
            granularity=granularity,
            metrics=metrics
        )

        if total_cost == 0.0:
            results.append({
                "tag_key": tag_key,
                "tag_value": tag_value,
                "stack_name": stack_name,
                "error": "No cost data available"
            })
            continue

        budget_status = "over_budget" if total_cost >= total_budget else "within_budget"

        results.append({
            "tag_key": tag_key,
            "tag_value": tag_value,
            "total_cost": total_cost,
            "total_budget": total_budget,
            "stack_name": stack_name,
            "status": budget_status
        })

        if budget_status == "over_budget":
            print(f"🚨 Cost exceeded for {tag_value}. Deleting stack {stack_name}.")
            delete_stack(stack_name)

    # Compose beautified plain text email
    print("📝 Composing plain text report...")
    report_date = datetime.utcnow().date()
    lines = []

    deleted_stacks = []
    no_data_tags = []

    lines.append(f"AWS Daily Cost Report 📊 - {report_date}")
    lines.append("=" * 112)
    lines.append("")

    # Section: Cost Summary
    lines.append("COST SUMMARY REPORT")
    lines.append("-" * 112)
    table_header = (
        f"| {'Tag Key':<15} | {'Tag Value':<18} | {'Stack Name':<22} | "
        f"{'Cost ($)':>9} | {'Budget ($)':>10} | {'Used %':>7} | Status         |"
    )
    table_border = "-" * len(table_header)
    lines.append(table_border)
    lines.append(table_header)
    lines.append(table_border)

    for r in results:
        tag_key = r.get('tag_key', 'N/A')
        tag_value = r.get('tag_value')
        stack_name = r.get('stack_name')

        if "error" in r:
            line = (
                f"| {tag_key:<15} | {tag_value:<18} | {stack_name:<22} | {'-':>9} | {'-':>10} | {'-':>7} | ❌ {r['error']:<12} |"
            )
            no_data_tags.append((tag_key, tag_value, stack_name, r['error']))
        else:
            cost = r['total_cost']
            budget = r['total_budget']
            percent_used = (cost / budget * 100) if budget > 0 else 0
            status_icon = "⚠️" if r["status"] == "over_budget" else "✅"
            status_text = "Over Budget" if r["status"] == "over_budget" else "Within Budget"
            line = (
                f"| {tag_key:<15} | {tag_value:<18} | {stack_name:<22} | {cost:>9.2f} | "
                f"{budget:>10.2f} | {percent_used:>6.1f}% | {status_icon} {status_text:<12} |"
            )
            if r["status"] == "over_budget":
                deleted_stacks.append(stack_name)

        lines.append(line)

    lines.append(table_border)
    lines.append("")

    # Section: Stacks Deleted
    lines.append("STACKS DELETED TODAY")
    lines.append("-" * 112)
    if deleted_stacks:
        for s in deleted_stacks:
            lines.append(f"🗑️ {s}")
    else:
        lines.append("✅ No stacks deleted today.")
    lines.append("")

    # Section: No Data Tags
    lines.append("NO COST DATA AVAILABLE")
    lines.append("-" * 112)
    if no_data_tags:
        for tag_key, tag_value, stack_name, reason in no_data_tags:
            lines.append(f"  Tag '{tag_key}:{tag_value}' (Stack: {stack_name}) - {reason}")
    else:
        lines.append("✅ All tags reported valid cost data.")
    lines.append("")

    # Footer
    lines.append("=" * 112)
    lines.append("Legend: ✅ = Within Budget, ⚠️ = Over Budget, ❌ = Error, 🗑️ = Stack Deleted")
    lines.append("=" * 112)

    message = "\n".join(lines)
    subject = f"AWS Daily Cost Report - {report_date}"

    print("📧 Subject:", subject)
    print("📧 Message:\n", message)

    send_notification(subject, message)
    return {"status": "success", "data": results}
