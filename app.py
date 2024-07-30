from flask import Flask, request, render_template,render_template_string, redirect, url_for, jsonify, Response  
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import base64

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Конфигурация подключения к базе данных MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://login:password@localhost/database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Создаем экземпляр SQLAlchemy для работы с базой данных
db = SQLAlchemy(app) 

# Определяем модель данных для таблицы 'data'
class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    x1 = db.Column(db.Float, nullable=True)
    y1 = db.Column(db.Float, nullable=True)
    x2 = db.Column(db.Float, nullable=True)
    y2 = db.Column(db.Float, nullable=True)
    color = db.Column(db.String(255), nullable=True)

# Определяем модель данных для таблицы 'hex'
class Hex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    x1 = db.Column(db.Float, nullable=True)
    y1 = db.Column(db.Float, nullable=True)
    x2 = db.Column(db.Float, nullable=True)
    y2 = db.Column(db.Float, nullable=True)
    x3 = db.Column(db.Float, nullable=True)
    y3 = db.Column(db.Float, nullable=True)
    x4 = db.Column(db.Float, nullable=True)
    y4 = db.Column(db.Float, nullable=True)
    x5 = db.Column(db.Float, nullable=True)
    y5 = db.Column(db.Float, nullable=True)
    x6 = db.Column(db.Float, nullable=True)
    y6 = db.Column(db.Float, nullable=True)
    color = db.Column(db.String(255), nullable=True)

def gen_frames():
    camera = cv2.VideoCapture(1)  # Используем камеру с индексом 1
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = base64.b64encode(buffer).decode('utf-8')
            socketio.emit('video_frame', {'frame': frame_bytes})
            socketio.sleep(0.1)  # Небольшая задержка для стабильной передачи
    camera.release()


# Основная страница для выбора действия
@app.route('/')
def main_page():
    return render_template('front/second.html')

@app.route('/cam_page')
def cam_page():
    return render_template('cam.html')

# Страница для просмотра всех данных из таблицы 'data'
@app.route('/show_data')
def show_all_data():
    data_entries = Data.query.all()
    return render_template('show_data.html', data_entries=data_entries)

# Страница для добавления данных в таблицу 'data'
@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        data_content = request.form['data']
        new_data = Data(data=data_content)
        db.session.add(new_data)
        db.session.commit()
        return redirect(url_for('main_page'))  # Перенаправляем на основную страницу после добавления данных
    return render_template('add_data.html')

# Методы для работы с линиями
@app.route('/draw/line', methods=['GET'])
def get_all_lines_json():
    request_data = request.get_json(silent=True)

    if request_data and 'id' in request_data:
        data_id = request_data['id']
        data_entry = Data.query.get(data_id)
        if data_entry:
            data = {
                'id': data_entry.id,
                'time': data_entry.time,
                'x1': data_entry.x1,
                'y1': data_entry.y1,
                'x2': data_entry.x2,
                'y2': data_entry.y2,
                'color': data_entry.color
            }
            return jsonify(data)
        else:
            return jsonify({'error': 'Data not found'}), 404
    else:
        data_list = Data.query.all()
        data = [{'id': entry.id, 'time': entry.time, 'x1': entry.x1, 'y1': entry.y1, 'x2': entry.x2, 'y2': entry.y2, 'color': entry.color} for entry in data_list]
        return jsonify(data)

@app.route('/draw/line', methods=['POST'])
def post_line_to_db():
    request_data = request.get_json()

    if not request_data or not all(k in request_data for k in ('x1', 'y1', 'x2', 'y2', 'color')):
        return jsonify({'error': 'Data not provided or incorrect format'}), 400

    new_data = Data(
        x1=request_data['x1'],
        y1=request_data['y1'],
        x2=request_data['x2'],
        y2=request_data['y2'],
        color=request_data['color']
    )

    db.session.add(new_data)
    db.session.commit()

    added_data = Data.query.get(new_data.id)

    return jsonify({
        'id': added_data.id,
        'time': added_data.time,
        'x1': added_data.x1,
        'y1': added_data.y1,
        'x2': added_data.x2,
        'y2': added_data.y2,
        'color': added_data.color
    }), 201

@app.route('/draw/line', methods=['PUT'])
def update_line_in_db():
    request_data = request.get_json()

    if not request_data or 'id' not in request_data:
        return jsonify({'error': 'ID not provided or incorrect format'}), 400

    data_id = request_data['id']
    data_entry = Data.query.get(data_id)
    
    if not data_entry:
        return jsonify({'error': 'Data not found'}), 404

    if 'x1' in request_data:
        data_entry.x1 = request_data['x1']
    if 'y1' in request_data:
        data_entry.y1 = request_data['y1']
    if 'x2' in request_data:
        data_entry.x2 = request_data['x2']
    if 'y2' in request_data:
        data_entry.y2 = request_data['y2']
    if 'color' in request_data:
        data_entry.color = request_data['color']

    db.session.commit()

    updated_data = Data.query.get(data_id)

    return jsonify({
        'id': updated_data.id,
        'time': updated_data.time,
        'x1': updated_data.x1,
        'y1': updated_data.y1,
        'x2': updated_data.x2,
        'y2': updated_data.y2,
        'color': updated_data.color
    }), 200

@app.route('/draw/line', methods=['DELETE'])
def delete_line_from_db():
    request_data = request.get_json()

    if not request_data or 'id' not in request_data:
        return jsonify({'error': 'ID not provided or incorrect format'}), 400

    data_id = request_data['id']
    data_entry = Data.query.get(data_id)
    if not data_entry:
        return jsonify({'error': 'Data not found'}), 404

    db.session.delete(data_entry)
    db.session.commit()

    return jsonify({'message': 'Data deleted successfully'}), 200

# Методы для работы с шестигранниками
@app.route('/draw/hexagon', methods=['GET'])
def get_all_hexagons_json():
    request_data = request.get_json(silent=True)

    if request_data and 'id' in request_data:
        data_id = request_data['id']
        data_entry = Hex.query.get(data_id)
        if data_entry:
            data = {
                'id': data_entry.id,
                'time': data_entry.time,
                'x1': data_entry.x1,
                'y1': data_entry.y1,
                'x2': data_entry.x2,
                'y2': data_entry.y2,
                'x3': data_entry.x3,
                'y3': data_entry.y3,
                'x4': data_entry.x4,
                'y4': data_entry.y4,
                'x5': data_entry.x5,
                'y5': data_entry.y5,
                'x6': data_entry.x6,
                'y6': data_entry.y6,
                'color': data_entry.color
            }
            return jsonify(data)
        else:
            return jsonify({'error': 'Data not found'}), 404
    else:
        data_list = Hex.query.all()
        data = [{'id': entry.id, 'time': entry.time, 'x1': entry.x1, 'y1': entry.y1, 'x2': entry.x2, 'y2': entry.y2,
                 'x3': entry.x3, 'y3': entry.y3, 'x4': entry.x4, 'y4': entry.y4, 'x5': entry.x5, 'y5': entry.y5,
                 'x6': entry.x6, 'y6': entry.y6, 'color': entry.color} for entry in data_list]
        return jsonify(data)

@app.route('/draw/hexagon', methods=['POST'])
def post_hexagon_to_db():
    request_data = request.get_json()

    if not request_data or not all(k in request_data for k in ('x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4', 'x5', 'y5', 'x6', 'y6', 'color')):
        return jsonify({'error': 'Data not provided or incorrect format'}), 400

    new_data = Hex(
        x1=request_data['x1'],
        y1=request_data['y1'],
        x2=request_data['x2'],
        y2=request_data['y2'],
        x3=request_data['x3'],
        y3=request_data['y3'],
        x4=request_data['x4'],
        y4=request_data['y4'],
        x5=request_data['x5'],
        y5=request_data['y5'],
        x6=request_data['x6'],
        y6=request_data['y6'],
        color=request_data['color']
    )

    db.session.add(new_data)
    db.session.commit()

    added_data = Hex.query.get(new_data.id)

    return jsonify({
        'id': added_data.id,
        'time': added_data.time,
        'x1': added_data.x1,
        'y1': added_data.y1,
        'x2': added_data.x2,
        'y2': added_data.y2,
        'x3': added_data.x3,
        'y3': added_data.y3,
        'x4': added_data.x4,
        'y4': added_data.y4,
        'x5': added_data.x5,
        'y5': added_data.y5,
        'x6': added_data.x6,
        'y6': added_data.y6,
        'color': added_data.color
    }), 201

@app.route('/draw/hexagon', methods=['PUT'])
def update_hexagon_in_db():
    request_data = request.get_json()

    if not request_data or 'id' not in request_data:
        return jsonify({'error': 'ID not provided or incorrect format'}), 400

    data_id = request_data['id']
    data_entry = Hex.query.get(data_id)
    
    if not data_entry:
        return jsonify({'error': 'Data not found'}), 404

    if 'x1' in request_data:
        data_entry.x1 = request_data['x1']
    if 'y1' in request_data:
        data_entry.y1 = request_data['y1']
    if 'x2' in request_data:
        data_entry.x2 = request_data['x2']
    if 'y2' in request_data:
        data_entry.y2 = request_data['y2']
    if 'x3' in request_data:
        data_entry.x3 = request_data['x3']
    if 'y3' in request_data:
        data_entry.y3 = request_data['y3']
    if 'x4' in request_data:
        data_entry.x4 = request_data['x4']
    if 'y4' in request_data:
        data_entry.y4 = request_data['y4']
    if 'x5' in request_data:
        data_entry.x5 = request_data['x5']
    if 'y5' in request_data:
        data_entry.y5 = request_data['y5']
    if 'x6' in request_data:
        data_entry.x6 = request_data['x6']
    if 'y6' in request_data:
        data_entry.y6 = request_data['y6']
    if 'color' in request_data:
        data_entry.color = request_data['color']

    db.session.commit()

    updated_data = Hex.query.get(data_id)

    return jsonify({
        'id': updated_data.id,
        'time': updated_data.time,
        'x1': updated_data.x1,
        'y1': updated_data.y1,
        'x2': updated_data.x2,
        'y2': updated_data.y2,
        'x3': updated_data.x3,
        'y3': updated_data.y3,
        'x4': updated_data.x4,
        'y4': updated_data.y4,
        'x5': updated_data.x5,
        'y5': updated_data.y5,
        'x6': updated_data.x6,
        'y6': updated_data.y6,
        'color': updated_data.color
    }), 200

@app.route('/draw/hexagon', methods=['DELETE'])
def delete_hexagon_from_db():
    request_data = request.get_json()

    if not request_data or 'id' not in request_data:
        return jsonify({'error': 'ID not provided or incorrect format'}), 400

    data_id = request_data['id']
    data_entry = Hex.query.get(data_id)
    if not data_entry:
        return jsonify({'error': 'Data not found'}), 404

    db.session.delete(data_entry)
    db.session.commit()

    return jsonify({'message': 'Data deleted successfully'}), 200

if __name__ == '__main__':
    socketio.start_background_task(gen_frames)
    socketio.run(app, host='0.0.0.0', port=5000)
