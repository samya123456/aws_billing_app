aws lambda invoke --function-name CostMonitoringLambda output.json

# for ((i=1; i<=100; i++))
# do
#   aws lambda invoke --function-name CostMonitoringLambda output_file.json
#   echo "Invocation $i completed."
# done