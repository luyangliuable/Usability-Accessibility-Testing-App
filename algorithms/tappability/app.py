'''
api to run algorithm from HTTP
'''
from flask import Flask, request, jsonify
import subprocess


app = Flask(__name__)

# home route
@app.route('/')
def home():
    return "Owleye app is live."

# run algorithm
@app.route("/execute", methods=["POST"])
def execute():
    if request.method != "POST":
        return 'error'

    try:
        image_dir = request.get_json()["image_dir"]
        layout_dir = request.get_json()["layout_dir"]
        output_dir = request.get_json()["output_dir"]
        
        print('STARTING TAPSHOE %s %s %s' % (image_dir, layout_dir, output_dir))
        
        subprocess.run(["python3", "/home/tappable/pipeline.py", image_dir, layout_dir, output_dir])
        
        return jsonify( {"result": "SUCCESS"} ), 200
        
    except Exception as e:
        return str(e)
    
if __name__=='__main__':
    app.run(debug=True, host="0.0.0.0", port=3007)