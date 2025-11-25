from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 简单的路由测试
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("健康检查被调用")
    return jsonify({
        "status": "healthy", 
        "service": "Material AI",
        "timestamp": "2024-01-01T00:00:00Z"
    })

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"message": "API测试成功", "code": 200})

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "端点未找到"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500

# Vercel需要这个
app = app
