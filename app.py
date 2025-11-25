from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging
import requests
import json
from datetime import datetime
from github import Github
from PyPDF2 import PdfReader
import docx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 配置 - 使用你的DeepSeek API密钥
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-f710c8af140444d78c035adc34aab2b6')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 初始化客户端
github_client = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None

class DeepSeekAI:
    @staticmethod
    def generate_answer(question, context=None):
        """使用DeepSeek API生成回答"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            
            system_prompt = """你是一个专业的材料科学专家，擅长用通俗易懂的方式解释复杂的材料科学概念。请根据用户的问题提供：
1. 核心概念的专业解释
2. 实际应用场景
3. 相关材料类型和特性
4. 进一步学习建议

请用中文回答，保持专业但易于理解。"""
            
            user_content = f"问题：{question}"
            if context:
                user_content += f"\n\n相关上下文：{context}"
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": False
            }
            
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API请求错误: {e}")
            return f"抱歉，AI服务暂时不可用。错误: {str(e)}"
        except Exception as e:
            logger.error(f"DeepSeek API处理错误: {e}")
            return f"处理AI回答时出现错误: {str(e)}"
    
    @staticmethod
    def analyze_question(question):
        """分析材料科学问题"""
        # 这里可以添加更复杂的问题分析逻辑
        material_keywords = {
            "金属材料": ["合金", "钢铁", "铝", "铜", "钛", "镁", "镍", "锌", "金属间化合物"],
            "高分子材料": ["聚合物", "塑料", "橡胶", "纤维", "高分子", "PMMA", "PE", "PP", "PVC"],
            "陶瓷材料": ["陶瓷", "氧化铝", "氧化锆", "碳化硅", "氮化硅", "功能陶瓷", "结构陶瓷"],
            "复合材料": ["复合材料", "纤维增强", "层压", "CFRP", "GFRP", "金属基复合材料"],
            "纳米材料": ["纳米", "石墨烯", "碳纳米管", "量子点", "纳米线", "纳米颗粒"],
            "能源材料": ["电池", "燃料电池", "太阳能", "储能", "锂离子", "光伏"],
            "生物材料": ["生物相容性", "医用材料", "组织工程", "药物输送", "生物降解"]
        }
        
        detected_categories = []
        for category, keywords in material_keywords.items():
            if any(keyword in question.lower() for keyword in keywords):
                detected_categories.append(category)
        
        return {
            "categories": detected_categories if detected_categories else ["通用材料科学"],
            "complexity": "高级" if any(word in question for word in ["机理", "原理", "机制", "理论"]) else "中级",
            "suggested_sources": ["材料科学基础教材", "学术论文数据库", "专业期刊", "实验数据"],
            "key_concepts": ["材料性能", "加工工艺", "应用领域", "测试方法"]
        }

class MaterialScienceAI:
    @staticmethod
    def get_answer(question):
        """获取材料科学问题的AI回答"""
        # 先分析问题
        analysis = DeepSeekAI.analyze_question(question)
        
        # 使用DeepSeek生成回答
        answer = DeepSeekAI.generate_answer(question)
        
        return {
            "answer": answer,
            "analysis": analysis
        }

class GitHubAnalyzer:
    @staticmethod
    def analyze_repository(repo_url):
        """分析GitHub材料科学仓库"""
        if not github_client:
            return {"error": "GitHub API未配置"}
        
        try:
            # 提取仓库信息
            if "github.com/" in repo_url:
                repo_name = repo_url.split("github.com/")[1].strip("/")
            else:
                repo_name = repo_url
            
            repo = github_client.get_repo(repo_name)
            
            # 获取仓库内容
            contents = []
            material_keywords = ["material", "合金", "polymer", "ceramic", "composite", "纳米", "coating", "电池", "能源"]
            material_files = []
            
            try:
                for content in repo.get_contents(""):
                    if content.type == "file":
                        contents.append(content.name)
                        if any(keyword in content.name.lower() for keyword in material_keywords):
                            material_files.append(content.name)
            except:
                pass
            
            # 分析仓库
            analysis = {
                "repo_info": {
                    "name": repo.full_name,
                    "description": repo.description,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "topics": repo.get_topics(),
                    "url": repo.html_url
                },
                "material_analysis": {
                    "is_material_related": len(material_files) > 0 or any(
                        keyword in (repo.description or "").lower() for keyword in material_keywords
                    ),
                    "material_files": material_files,
                    "total_files": len(contents),
                    "material_score": len(material_files) / max(len(contents), 1)
                },
                "activity": {
                    "created_at": repo.created_at.isoformat(),
                    "updated_at": repo.updated_at.isoformat(),
                    "open_issues": repo.open_issues_count,
                    "last_commit": repo.pushed_at.isoformat()
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"GitHub分析错误: {e}")
            return {"error": f"分析仓库失败: {str(e)}"}

class DocumentProcessor:
    @staticmethod
    def process_file(file):
        """处理上传的文档"""
        try:
            filename = file.filename.lower()
            content = ""
            
            if filename.endswith('.pdf'):
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        content += text + "\n"
                        
            elif filename.endswith('.docx'):
                doc = docx.Document(file)
                for paragraph in doc.paragraphs:
                    if paragraph.text:
                        content += paragraph.text + "\n"
                        
            elif filename.endswith('.txt'):
                content = file.read().decode('utf-8')
                
            elif filename.endswith('.md'):
                content = file.read().decode('utf-8')
                
            else:
                return {"error": "不支持的文件格式"}
            
            # 分析文档内容
            analysis = DocumentProcessor.analyze_content(content)
            return analysis
            
        except Exception as e:
            logger.error(f"文档处理错误: {e}")
            return {"error": f"处理文档失败: {str(e)}"}
    
    @staticmethod
    def analyze_content(content):
        """分析文档内容"""
        material_keywords = {
            "金属材料": ["合金", "钢铁", "铝", "铜", "钛", "镁", "镍", "锌", "金属间化合物", "热处理", "淬火"],
            "高分子材料": ["聚合物", "塑料", "橡胶", "纤维", "高分子", "PMMA", "PE", "PP", "PVC", "聚合", "共聚"],
            "陶瓷材料": ["陶瓷", "氧化铝", "氧化锆", "碳化硅", "氮化硅", "功能陶瓷", "结构陶瓷", "烧结"],
            "复合材料": ["复合材料", "纤维增强", "层压", "CFRP", "GFRP", "金属基复合材料", "界面"],
            "纳米材料": ["纳米", "石墨烯", "碳纳米管", "量子点", "纳米线", "纳米颗粒", "自组装"],
            "能源材料": ["电池", "燃料电池", "太阳能", "储能", "锂离子", "光伏", "电极", "电解质"],
            "生物材料": ["生物相容性", "医用材料", "组织工程", "药物输送", "生物降解", "植入材料"]
        }
        
        found_categories = []
        keyword_counts = {}
        
        for category, keywords in material_keywords.items():
            count = sum(1 for keyword in keywords if keyword in content)
            if count > 0:
                found_categories.append(category)
                keyword_counts[category] = count
        
        return {
            "length": len(content),
            "categories": found_categories,
            "keyword_density": keyword_counts,
            "summary": content[:300] + "..." if len(content) > 300 else content,
            "page_count": len(content) // 1500 + 1  # 估算页数
        }

# 材料科学知识库
MATERIALS_KNOWLEDGE = {
    "categories": ["金属材料", "高分子材料", "陶瓷材料", "复合材料", "纳米材料", "能源材料", "生物材料"],
    "properties": ["力学性能", "热学性能", "电学性能", "光学性能", "磁学性能", "化学稳定性"],
    "processes": ["铸造", "锻造", "焊接", "热处理", "3D打印", "粉末冶金", "注塑成型"],
    "characterization": ["SEM", "TEM", "XRD", "DSC", "TGA", "力学测试", "光谱分析"]
}

# 路由定义
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Material Science AI (DeepSeek)",
        "timestamp": datetime.now().isoformat(),
        "ai_provider": "DeepSeek",
        "features": ["AI问答", "GitHub分析", "文档处理"]
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """材料科学AI对话 - 使用DeepSeek"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "问题不能为空"}), 400
        
        # 使用DeepSeek生成回答
        result = MaterialScienceAI.get_answer(question)
        
        response = {
            "question": question,
            "answer": result["answer"],
            "analysis": result["analysis"],
            "sources": result["analysis"]["suggested_sources"],
            "ai_model": "DeepSeek",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"DeepSeek问答: {question}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"聊天错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/github/analyze', methods=['POST'])
def analyze_github():
    """分析GitHub材料科学仓库"""
    try:
        data = request.json
        repo_url = data.get('repo_url', '').strip()
        
        if not repo_url:
            return jsonify({"error": "仓库URL不能为空"}), 400
        
        analysis = GitHubAnalyzer.analyze_repository(repo_url)
        
        response = {
            "repo_url": repo_url,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"GitHub分析错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/process', methods=['POST'])
def process_document():
    """处理材料科学文档"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "没有选择文件"}), 400
        
        result = DocumentProcessor.process_file(file)
        
        response = {
            "filename": file.filename,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"文档处理错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/materials/knowledge', methods=['GET'])
def get_materials_knowledge():
    """获取材料科学知识库"""
    return jsonify(MATERIALS_KNOWLEDGE)

@app.route('/api/deepseek/status', methods=['GET'])
def deepseek_status():
    """检查DeepSeek API状态"""
    try:
        # 简单的API测试
        test_question = "什么是材料科学？"
        answer = DeepSeekAI.generate_answer(test_question)
        
        return jsonify({
            "status": "connected",
            "model": "deepseek-chat",
            "response_length": len(answer),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "端点未找到"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500

if __name__ == '__main__':
    app.run(debug=True)
else:
    app = app
