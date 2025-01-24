import index


class DummyContext:
    def __init__(self):
        self.function_name = "dummy_function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:dummy-region:123456789012:function:dummy_function"
        self.aws_request_id = "dummy-request-id"

def test_lambda_handler():
    # Dummy event object
    event = {
        "name": "TestUser"
    }
    
    # Dummy context object
    context = DummyContext()
    
    # Call the lambda handler
    index.lambda_handler(event, context)


# Run the test function
test_lambda_handler()

