export PORT=5000
pip install -r requirements.txt
python /opt/dmarc/redis_worker.py & gunicorn -w 2 -b 0.0.0.0:$PORT  'dmarc_toolkit:app'