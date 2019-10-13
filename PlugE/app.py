from flask import Flask, request, abort, jsonify


from plugs import Plugs

app = Flask(__name__)
p = Plugs()


@app.route('/start', methods=['POST'])
def start():
    if not 'name' in request.json:
        abort(400, "Must pass the FitHome monitor name.")

    monitor_name = request.json['name']
    p.start(monitor_name, 1)

    return jsonify({"name": monitor_name})


@app.route('/stop')
def stop():
    p.stop()
    return jsonify(success=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8519, debug=True)
