from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import logging
from datetime import datetime
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
YOUR_DATABASE_API_URL = os.getenv('YOUR_DATABASE_API_URL', '')  # 您的数据库API地址
YOUR_DATABASE_API_KEY = os.getenv('YOUR_DATABASE_API_KEY', '')  # 您的数据库API密钥

class MaterialAIService:
    def __init__(self):
        self.system_prompt = """你是一个专业的材料科学专家，专门回答材料科学相关的问题。

请基于材料科学原理提供专业、准确、实用的回答，包括：

1. 材料性能分析（力学性能、热学性能、电学性能等）
2. 材料选择建议（基于应用场景和性能要求）
3. 加工工艺咨询（制造方法、处理工艺）
4. 应用场景分析（不同领域的材料应用）
5. 参数计算和预测

回答要求：
- 科学准确：基于材料科学原理和事实数据
- 具体详细：提供具体的参数、数据和应用建议  
- 实用导向：给出实际应用中的注意事项和建议
- 结构清晰：分点说明，便于理解

用中文回答，保持专业但易于理解。"""

    def get_ai_response(self, question):
        """获取DeepSeek AI回答"""
        try:
            # 优先使用DeepSeek官方API
            if DEEPSEEK_API_KEY:
                return self._call_deepseek_official(question)
            # 备用OpenRouter
            elif OPENROUTER_API_KEY:
                return self._call_deepseek_openrouter(question)
            else:
                return self._get_fallback_response(question)
        except Exception as e:
            logger.error(f"AI服务错误: {str(e)}")
            return "抱歉，AI服务暂时不可用，请稍后重试。"

    def _call_deepseek_official(self, question):
        """调用DeepSeek官方API"""
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question}
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
            "stream": False
        }
        
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"DeepSeek API错误: {response.status_code}")
                return self._call_deepseek_openrouter(question)
                
        except Exception as e:
            logger.error(f"DeepSeek官方API异常: {str(e)}")
            return self._call_deepseek_openrouter(question)

    def _call_deepseek_openrouter(self, question):
        """通过OpenRouter调用DeepSeek"""
        if not OPENROUTER_API_KEY:
            return self._get_fallback_response(question)
            
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://material-ai.vercel.app",
            "X-Title": "材料科学AI问答"
        }
        
        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenRouter API错误: {response.status_code}")
                return self._get_fallback_response(question)
                
        except Exception as e:
            logger.error(f"OpenRouter API异常: {str(e)}")
            return self._get_fallback_response(question)

    def _get_fallback_response(self, question):
        """降级响应"""
        return f"""关于"{question}"，这是一个很好的材料科学问题！

由于当前AI服务配置限制，我无法提供完整的专业回答。建议：

1. 配置DeepSeek API密钥获得完整功能
2. 或直接访问 chat.deepseek.com 进行咨询

我可以帮助分析材料性能、选择建议、工艺咨询等问题。"""

class DatabaseService:
    def __init__(self):
        self.api_url = YOUR_DATABASE_API_URL
        self.api_key = YOUR_DATABASE_API_KEY

    def query_materials(self, params):
        """查询材料数据 - 连接到您的数据库API"""
        if not self.api_url:
            return {"error": "数据库API未配置", "available": False}
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = requests.post(
                f"{self.api_url}/query",
                json=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"数据库查询失败: {response.status_code}", "available": True}
                
        except Exception as e:
            return {"error": f"数据库连接失败: {str(e)}", "available": True}

    def get_material_properties(self, material_name):
        """获取材料性能数据"""
        return self.query_materials({
            "action": "get_material_properties",
            "material_name": material_name
        })

    def search_materials_by_properties(self, properties):
        """根据性能搜索材料"""
        return self.query_materials({
            "action": "search_by_properties",
            "properties": properties
        })

# 初始化服务
ai_service = MaterialAIService()
db_service = DatabaseService()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """智能问答接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
            
        question = data.get('question', '').strip()
        if not question:
            return jsonify({"error": "问题不能为空"}), 400

        logger.info(f"收到材料科学问题: {question}")

        # 获取AI回答
        answer = ai_service.get_ai_response(question)
        
        # 尝试从数据库获取相关数据
        db_data = {}
        if any(keyword in question.lower() for keyword in ['性能', '参数', '密度', '强度']):
            db_data = db_service.get_material_properties(question)

        response_data = {
            "success": True,
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "database_connected": db_service.api_url != "",
            "database_data": db_data
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500

@app.route('/api/database/query', methods=['POST'])
def database_query():
    """数据库查询接口 - 连接到您的专业数据库"""
    try:
        data = request.get_json()
        query_type = data.get('query_type')
        parameters = data.get('parameters', {})
        
        if query_type == 'material_properties':
            result = db_service.get_material_properties(parameters.get('material_name'))
        elif query_type == 'search_materials':
            result = db_service.search_materials_by_properties(parameters.get('properties', {}))
        else:
            result = {"error": "不支持的查询类型"}
        
        return jsonify({
            "success": True,
            "query_type": query_type,
            "result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/database/test', methods=['GET'])
def test_database():
    """测试数据库连接"""
    test_result = db_service.get_material_properties("304不锈钢")
    return jsonify({
        "database_configured": db_service.api_url != "",
        "test_query": "304不锈钢",
        "result": test_result
    })

@app.route('/api/materials/search', methods=['POST'])
def search_materials():
    """材料搜索接口"""
    try:
        data = request.get_json()
        search_criteria = data.get('criteria', {})
        
        result = db_service.search_materials_by_properties(search_criteria)
        
        return jsonify({
            "success": True,
            "search_criteria": search_criteria,
            "results": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    ai_available = bool(DEEPSEEK_API_KEY or OPENROUTER_API_KEY)
    db_configured = bool(YOUR_DATABASE_API_URL)
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "材料科学AI问答网站",
        "ai_service_available": ai_available,
        "database_configured": db_configured,
        "deployed": True,
        "version": "2.0.0"
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息（不包含敏感信息）"""
    return jsonify({
        "ai_service": "DeepSeek",
        "database_integration": True,
        "features": [
            "材料科学智能问答",
            "专业数据库集成", 
            "性能参数查询",
            "材料推荐系统",
            "公开访问"
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)