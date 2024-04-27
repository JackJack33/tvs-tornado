import matplotlib.pyplot as plt
from datetime import datetime
# Example counts dictionary
counts = {
    2023: {
        1: {'SEVERE THUNDERSTORM': 5, 'TORNADO': 10},
        2: {'SEVERE THUNDERSTORM': 8, 'FLASH FLOOD': 3}
    },
    2024: {
        3: {'TORNADO': 6, 'FLASH FLOOD': 7},
        4: {'SEVERE THUNDERSTORM': 4, 'TORNADO': 2}
    }
}

start = "2022-1-1 00:00:00"
end = "2025-1-1 00:00:00"

start_timestamp = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
end_timestamp = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")



# Initialize lists to store data for plotting
months = []
warning_types = set()  # Use a set to collect unique warning types
for year in range(start_timestamp.year, end_timestamp.year + 1):
    for month in range(1, 13):  # Iterate over all months
        months.append(datetime(year, month, 1))  # Assuming the first day of each month for simplicity
        try:
            for warning_type in counts[year][month]:
                warning_types.add(warning_type)
        except Exception as e:
            print(e)

fig = plt.figure(figsize=(10, 6))
for warning_type in warning_types:
    counts_list = []
    for month in months:
        year = month.year
        month_num = month.month
        try:
            counts_list.append(counts[year][month_num].get(warning_type, 0))
        except Exception as e:
            print(e)
    plt.plot(months, counts_list, label=warning_type)

plt.xlabel('Time')
plt.ylabel('Count')
plt.title('Event Counts Over Time')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.show()
