from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Material AI - 运行中</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-lg shadow-lg text-center">
            <h1 class="text-2xl font-bold text-green-600 mb-4">✅ Material AI 运行成功！</h1>
            <p class="text-gray-600">基础 Flask 应用已在 Vercel 上成功部署</p>
            <div class="mt-4 space-y-2">
                <a href="/api/health" class="block bg-blue-500 text-white px-4 py-2 rounded">健康检查</a>
                <a href="/api/test" class="block bg-green-500 text-white px-4 py-2 rounded">功能测试</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy", 
        "service": "Material AI",
        "deployment": "successful"
    })

@app.route('/api/test')
def test():
    return jsonify({"message": "API 测试成功", "timestamp": "2024-01-01"})

# 移除所有复杂导入和功能
# 先让基础版本工作

if __name__ == '__main__':
    app.run()
else:
    app = app