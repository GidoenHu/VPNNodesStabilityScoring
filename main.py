import csv
from collections import defaultdict
import statistics
import matplotlib.pyplot as plt
import os

def parse_value(value):
    if value == '' or value.upper() == 'ERROR':
        return None
    try:
        return float(value)
    except ValueError:
        return None

def read_csv_files(dir_path):
    data = defaultdict(lambda: defaultdict(list))
    file_names = []
    for filename in sorted(os.listdir(dir_path)):
        if filename.endswith('.csv'):
            file_path = os.path.join(dir_path, filename)
            file_names.append(filename)
            
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) == 3:
                        server_name, ping, speed = row
                        ping_value = parse_value(ping)
                        speed_value = parse_value(speed)
                        if ping_value is not None and speed_value is not None:
                            data[server_name][filename].append((ping_value, speed_value))
                        elif ping_value is None and speed_value is None:
                            data[server_name][filename].append(('ERROR', 'ERROR'))
    return data, file_names

def calculate_scores(measurements):
    valid_measurements = [m for m in measurements if m != ('ERROR', 'ERROR')]
    if len(valid_measurements) < 2:
        return 0, 0, float('inf')  # Stability score, avg speed, avg ping

    pings, speeds = zip(*valid_measurements)
    
    # Stability score (lower variation is better for both ping and speed)
    ping_stability = 1 / (statistics.stdev(pings) + 1)
    speed_stability = 1 / (statistics.stdev(speeds) / statistics.mean(speeds) + 1)
    stability_score = (ping_stability + speed_stability) / 2

    avg_speed = statistics.mean(speeds)
    avg_ping = statistics.mean(pings)

    return stability_score, avg_speed, avg_ping

def rank_nodes(data):
    rankings = []
    for server_name, file_measurements in data.items():
        all_measurements = [m for file_ms in file_measurements.values() for m in file_ms]
        stability_score, avg_speed, avg_ping = calculate_scores(all_measurements)
        
        # Normalize scores
        normalized_stability = stability_score / 1  # Assuming stability_score is already between 0 and 1
        normalized_speed = min(avg_speed / 100, 1)  # Assuming 100 Mbps is the best possible speed
        normalized_ping = max(1 - avg_ping / 1000, 0)  # Assuming 1000 ms is the worst possible ping

        # Calculate weighted score
        weighted_score = (4 * normalized_stability + 3 * normalized_speed + 1 * normalized_ping) / 8

        rankings.append((server_name, weighted_score, stability_score, avg_speed, avg_ping))
    
    return sorted(rankings, key=lambda x: x[1], reverse=True)

def visualize_performance(data, file_names):
    # Prepare data for plotting
    ping_data = defaultdict(list)
    speed_data = defaultdict(list)
    error_data = defaultdict(list)
    
    for server_name, file_measurements in data.items():
        for filename in file_names:
            measurements = file_measurements.get(filename, [])
            valid_measurements = [m for m in measurements if m != ('ERROR', 'ERROR')]
            error_count = len(measurements) - len(valid_measurements)
            
            if valid_measurements:
                pings, speeds = zip(*valid_measurements)
                ping_data[server_name].append(statistics.mean(pings))
                speed_data[server_name].append(statistics.mean(speeds))
            else:
                ping_data[server_name].append(None)
                speed_data[server_name].append(None)
            
            error_data[server_name].append(error_count)

    # Plotting
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(20, 30))  # Increased figure size
    fig.suptitle('VPN Nodes Performance Over Time', fontsize=16)

    # Function to plot data
    def plot_data(ax, data, title, ylabel, color_map):
        for i, (server_name, values) in enumerate(data.items()):
            color = plt.cm.get_cmap(color_map)(i / len(data))
            ax.plot(range(len(file_names)), values, '-', label=server_name, color=color, linewidth=1.5, alpha=0.7)
        
        ax.set_title(title, fontsize=14)
        ax.set_xlabel('File Name', fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xticks(range(len(file_names)))
        ax.set_xticklabels(file_names, rotation=45, ha='right')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)

    plot_data(ax1, ping_data, 'Ping Performance', 'Average Ping (ms)', 'viridis')
    plot_data(ax2, speed_data, 'Speed Performance', 'Average Speed (Mbps)', 'plasma')
    plot_data(ax3, error_data, 'Error Occurrences', 'Error Count', 'cividis')

    plt.tight_layout()
    plt.savefig('vpn_nodes_performance.png', dpi=300, bbox_inches='tight')
    plt.close()

def main(dir_path):
    data, file_names = read_csv_files(dir_path)
    rankings = rank_nodes(data)
    
    print("Node Performance Rankings:")
    print("{:<4} {:<30} {:<15} {:<15} {:<15} {:<15}".format(
        "Rank", "Node", "Weighted Score", "Stability Score", "Avg Speed (Mbps)", "Avg Ping (ms)"))
    print("-" * 95)
    for i, (node, weighted_score, stability_score, avg_speed, avg_ping) in enumerate(rankings, 1):
        print("{:<4} {:<30} {:<15.4f} {:<15.4f} {:<15.2f} {:<15.2f}".format(
            i, node, weighted_score, stability_score, avg_speed, avg_ping))

    visualize_performance(data, file_names)
    print("\nPerformance graph has been saved as 'vpn_nodes_performance.png'.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_csv_directory>")
        sys.exit(1)
    
    dir_path = sys.argv[1]
    if not os.path.isdir(dir_path):
        print(f"Error: {dir_path} is not a valid directory")
        sys.exit(1)
    
    main(dir_path)