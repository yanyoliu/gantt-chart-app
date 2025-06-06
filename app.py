from flask import Flask, request, send_file, jsonify, render_template
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import io
import os

app = Flask(__name__)
tasks = []
gantt_title = "我的甘特圖"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tasks', methods=['GET', 'POST', 'PUT'])
def manage_tasks():
    global tasks
    if request.method == 'GET':
        return jsonify(tasks)
    data = request.json
    if request.method == 'POST':
        tasks.append(data)
        return jsonify({"status": "created"})
    if request.method == 'PUT':
        task_id = data.get('id')
        for i, t in enumerate(tasks):
            if t.get('id') == task_id:
                tasks[i] = data
                break
        return jsonify({"status": "updated"})

@app.route('/title', methods=['POST'])
def set_title():
    global gantt_title
    gantt_title = request.json.get("title", gantt_title)
    return jsonify({"title": gantt_title})

@app.route('/export', methods=['GET'])
def export_chart():
    df = pd.DataFrame(tasks)
    if df.empty:
        return "沒有任務可供匯出", 400

    df['Start'] = pd.to_datetime(df['start'])
    df['Finish'] = pd.to_datetime(df['end'])

    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[(row['Finish'] - row['Start']).days],
            y=[row['name']],
            base=row['Start'],
            orientation='h',
            marker=dict(color=row['color']),
            name=row['name'],
            hovertemplate=f"{row['name']}<br>開始: {row['Start'].date()}<br>結束: {row['Finish'].date()}<extra></extra>"
        ))

    fig.update_layout(
        title=gantt_title,
        barmode='stack',
        xaxis=dict(title='時間', type='date', tickformat='%b %Y'),
        yaxis=dict(title='任務'),
        showlegend=False,
        height=500 + len(df) * 30,
        margin=dict(l=150)
    )

    format = request.args.get('format', 'png')
    buf = io.BytesIO()
    if format == 'png':
        fig.write_image(buf, format='png', scale=3)
        mime = 'image/png'
        ext = 'png'
    elif format == 'pdf':
        fig.write_image(buf, format='pdf')
        mime = 'application/pdf'
        ext = 'pdf'
    else:
        return "不支援的格式", 400
    buf.seek(0)
    return send_file(buf, mimetype=mime, as_attachment=True, download_name=f"gantt_chart.{ext}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
