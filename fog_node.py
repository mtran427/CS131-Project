import json
import sqlite3
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

class FogNode:
    def __init__(self):
        with open('config_dev.json', 'r') as file:
            self.config = json.load(file)
        with sqlite3.connect('fog_node.db') as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY,count INTEGER,event_type TEXT,timestamp TEXT,synced INTEGER)''')
        credential = self.config['firebase']['credentials_path']
        _credential = credentials.Certificate(credential)
        firebase_admin.initialize_app(_credential)
        self.app = Flask(__name__)

        @self.app.route('/events', methods=['POST'])
        def receive_event():
            data = request.get_json()
            count = data.get('count')
            event_type = data.get('event_type')
            print("Event received: " + event_type + " with count: " + str(count))
            conn = sqlite3.connect('fog_node.db')
            conn.execute('''INSERT INTO events (count, event_type, timestamp, synced)VALUES (?, ?, ?, 0)''', (count, event_type, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return jsonify({'status': 'received', 'timestamp': datetime.now().isoformat()})
    
    def sync_to_firebase(self):
        conn = sqlite3.connect('fog_node.db')
        events = conn.execute('''SELECT * FROM events WHERE synced = 0 ORDER BY timestamp LIMIT 100''').fetchall()
        if not events:
            print("No data to sync")
            conn.close()
            return
        batch = firestore.client().batch()
        synced = []
        for i in events:
            doc_data = {
                'count': i[1],
                'event_type': i[2],
                'timestamp': i[3],
                'fog_node_id': self.config['fog_node']['id']
            }
            batch.set(firestore.client().collection(self.config['firebase']['collections']['events']).document(), doc_data)
            synced.append(i[0])
        batch.commit()
        conn.execute('UPDATE events SET synced = 1 WHERE id IN (' + ','.join(['?' for _ in synced]) + ')', synced)
        conn.commit()
        conn.close()
        print("Synced " + str(len(synced)) + " events to Firebase")

if __name__ == '__main__':
    fog_node = FogNode()
    def synclooping():
        while True:
            fog_node.sync_to_firebase()
            time.sleep(fog_node.config['sync']['interval_seconds'])
    threading.Thread(target=synclooping, daemon=True).start()
    fog_node.app.run(
        host=fog_node.config['server']['host'],
        port=fog_node.config['server']['port'],
        debug=fog_node.config['server']['debug']
    ) 
