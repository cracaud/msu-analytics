from app import app          # 1. Create Dash instance
import components.layout     # 2. Register app.layout + sidebar toggle callback
import callbacks.routing     # 3. Register routing + sidebar filter callbacks

if __name__ == "__main__":
    app.run(debug=True) 