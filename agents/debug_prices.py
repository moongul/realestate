import sqlite3
import os

def check_data():
    # Use absolute path relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "real_estate.db")
    
    print(f"Checking DB at: {db_path}")
    if not os.path.exists(db_path):
        print("Error: Database file does not exist!")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("\n--- 구로구 (11530) raw_trades 샘플 ---")
    cur.execute("SELECT apt_name, trade_amount, trade_date, exclusive_area FROM raw_trades WHERE district_code = '11530' LIMIT 5")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- 강남구 (11680) raw_trades 샘플 ---")
    cur.execute("SELECT apt_name, trade_amount, trade_date, exclusive_area FROM raw_trades WHERE district_code = '11680' LIMIT 5")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- 구로구 district_trend 샘플 ---")
    cur.execute("SELECT * FROM district_trend WHERE district_code = '11530' ORDER BY log_date DESC LIMIT 5")
    for row in cur.fetchall():
        print(row)

    print("\n--- 강남구 district_trend 샘플 ---")
    cur.execute("SELECT * FROM district_trend WHERE district_code = '11680' ORDER BY log_date DESC LIMIT 5")
    for row in cur.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_data()
