import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dashboard.cli import CLIDashboard

def main():
    # Assuming news_data.json is in the root directory
    data_path = 'news_data.json'
    dashboard = CLIDashboard(data_path)
    dashboard.run()

if __name__ == '__main__':
    main()
