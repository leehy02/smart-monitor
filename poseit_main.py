from flask import Flask
from cbt_mode.cbt_server import cbt_server
from ai_mode.reset import reset
from ai_mode.report import report
from ai_mode.motor_control import motor_control
import openai

app = Flask(__name__)

app.register_blueprint(cbt_server)
app.register_blueprint(reset)
app.register_blueprint(report)
app.register_blueprint(motor_control)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
