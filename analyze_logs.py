import pandas as pd

def analyze_logs():
    logs = pd.read_csv('execution_logs.csv')
    logs = logs.dropna()
    success_logs = logs[logs['Status'] == 'SUCCESS']
    avg_execution_time = success_logs['Execution_Time_ms'].mean()
    print(f'Average Execution Time (ms) for SUCCESS tasks: {avg_execution_time}')

analyze_logs()
