import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import ollama
from dotenv import load_dotenv
from deploy_service import DeployService

load_dotenv()

app = FastAPI(title="GitHub Analyzer", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="front"), name="static")

# Initialize LLM clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
ollama_available = True  # Ollama runs locally

class GitHubAnalyzer:
    def __init__(self):
        self.automata_path = Path(__file__).parent.parent  # Path to main automata project
        print(f"Automata path: {self.automata_path}")
    
    async def analyze_repository(self, github_url: str) -> Dict[str, Any]:
        """Analyze GitHub repository using Amazing Automata and Mistral AI"""
        temp_dir = None
        try:
            # Check if repository is public
            is_public, repo_info = await self._check_repository_visibility(github_url)
            if not is_public:
                return {
                    "status": "private",
                    "message": "Репозиторий является приватным и не может быть проанализирован",
                    "repo_info": repo_info
                }
            
            # Clone repository
            temp_dir = await self._clone_repository(github_url)
            
            # Run Amazing Automata detection
            detected_info = self._run_automata_detect(temp_dir)
            
            # Get AI analysis
            ai_analysis = await self._get_llm_analysis(
                repo_info=repo_info,
                detected_info=detected_info,
                repo_path=temp_dir
            )
            
            return {
                "status": "success",
                "message": "Анализ завершен успешно",
                "repo_info": repo_info,
                "detected_info": detected_info,
                "ai_analysis": ai_analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при анализе: {str(e)}",
                "repo_info": {}
            }
        finally:
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except PermissionError:
                    # On Windows, git files might be locked
                    import time
                    time.sleep(0.1)
                    try:
                        shutil.rmtree(temp_dir)
                    except PermissionError:
                        print(f"Warning: Could not delete temp directory {temp_dir}")
    
    async def _check_repository_visibility(self, github_url: str) -> tuple[bool, Dict[str, Any]]:
        """Check if GitHub repository is public"""
        try:
            # Extract owner and repo from URL
            parts = github_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                raise ValueError("Invalid GitHub URL")
            
            owner, repo = parts[0], parts[1].replace(".git", "")
            
            # Check via GitHub API
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
                
                if response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Репозиторий не найден")
                
                if response.status_code == 403:
                    # Rate limited or private
                    return False, {"message": "Репозиторий недоступен (возможно приватный)"}
                
                repo_data = response.json()
                return not repo_data.get("private", True), repo_data
                
        except httpx.HTTPError:
            return False, {"message": "Ошибка при проверке репозитория"}
    
    async def _clone_repository(self, github_url: str) -> Path:
        """Clone repository to temporary directory"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Simple git clone (requires git to be installed)
            result = subprocess.run(
                ["git", "clone", "--depth", "1", github_url, str(temp_dir)],
                capture_output=True,
                text=True,
                check=True,
                timeout=60  # 60 second timeout
            )
            return temp_dir
        except subprocess.CalledProcessError as e:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            if "git" in e.stderr.lower() and "not found" in e.stderr.lower():
                raise HTTPException(status_code=400, detail="Git не установлен. Установите Git для клонирования репозиториев.")
            raise HTTPException(status_code=400, detail=f"Не удалось клонировать репозиторий: {e.stderr}")
        except subprocess.TimeoutExpired:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            raise HTTPException(status_code=400, detail="Таймаут при клонировании репозитория")
        except FileNotFoundError:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            raise HTTPException(status_code=400, detail="Git не найден. Установите Git для клонирования репозиториев.")
    
    def _run_automata_detect(self, repo_path: Path) -> Dict[str, Any]:
        """Run Amazing Automata detection on the repository"""
        try:
            # Set up environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.automata_path) + os.pathsep + env.get('PYTHONPATH', '')
            
            # Run automata detect
            cmd = [
                "python", "-m", "automata_cli.cli", "run", 
                "--cwd", str(repo_path), "--stage", "detect"
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            print(f"Working directory: {self.automata_path}")
            print(f"Repository path: {repo_path}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env,
                cwd=self.automata_path
            )
            
            print(f"Automata stdout: {result.stdout}")
            print(f"Automata stderr: {result.stderr}")
            
            return json.loads(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"Automata error: {e.stderr}")
            raise HTTPException(status_code=500, detail=f"Ошибка детекции: {e.stderr}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            raise HTTPException(status_code=500, detail="Ошибка парсинга результата детекции")
    
    async def _get_llm_analysis(self, repo_info: Dict[str, Any], detected_info: Dict[str, Any], repo_path: Path) -> Dict[str, Any]:
        """Get AI analysis using available LLM"""
        try:
            # Prepare context
            context = {
                "repo_name": repo_info.get("name", "Unknown"),
                "repo_description": repo_info.get("description", ""),
                "repo_language": repo_info.get("language", "Unknown"),
                "repo_stars": repo_info.get("stargazers_count", 0),
                "repo_url": repo_info.get("html_url", ""),
                "detected_languages": detected_info.get("languages", []),
                "file_count": detected_info.get("file_count", 0),
                "has_dockerfile": (repo_path / "Dockerfile").exists(),
                "has_requirements": (repo_path / "requirements.txt").exists(),
                "has_package_json": (repo_path / "package.json").exists(),
                "has_pom_xml": (repo_path / "pom.xml").exists(),
                "has_go_mod": (repo_path / "go.mod").exists(),
                "has_cargo_toml": (repo_path / "cargo.toml").exists(),
            }
            
            # Create prompt
            prompt = f"""
            Проанализируй следующий GitHub репозиторий и дай рекомендации по развертыванию и улучшению CI/CD пайплайна.
            
            Информация о репозитории:
            - Название: {context['repo_name']}
            - Описание: {context['repo_description']}
            - Основной язык: {context['repo_language']}
            - Звезды: {context['repo_stars']}
            - URL: {context['repo_url']}
            
            Обнаруженные технологии:
            - Языки программирования: {', '.join(context['detected_languages'])}
            - Количество файлов: {context['file_count']}
            - Dockerfile: {'Да' if context['has_dockerfile'] else 'Нет'}
            - requirements.txt: {'Да' if context['has_requirements'] else 'Нет'}
            - package.json: {'Да' if context['has_package_json'] else 'Нет'}
            - pom.xml: {'Да' if context['has_pom_xml'] else 'Нет'}
            - go.mod: {'Да' if context['has_go_mod'] else 'Нет'}
            - cargo.toml: {'Да' if context['has_cargo_toml'] else 'Нет'}
            
            Дай рекомендации по:
            1. Настройке CI/CD пайплайна
            2. Контейнеризации (Docker)
            3. Тестированию
            4. Развертыванию
            5. Безопасности
            6. Мониторингу
            
            Ответь в формате JSON с полями:
            - recommendations: массив строк с рекомендациями
            - files_to_add: массив объектов с полями name, content, description
            - deployment_plan: массив строк с планом развертывания
            - tech_stack_analysis: анализ технологического стека
            - priority_actions: приоритетные действия для улучшения
            """
            
            # Try different LLM providers in order of preference
            ai_response = None
            
            # 1. Try OpenAI
            if openai_client:
                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=2000,
                        temperature=0.7
                    )
                    ai_response = response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"OpenAI error: {e}")
            
            # 2. Try Ollama (local)
            if not ai_response and ollama_available:
                try:
                    response = ollama.chat(
                        model="llama3.2",  # or any other model you have
                        messages=[{"role": "user", "content": prompt}]
                    )
                    ai_response = response['message']['content'].strip()
                except Exception as e:
                    print(f"Ollama error: {e}")
            
            # 3. Fallback to basic analysis
            if not ai_response:
                return self._get_fallback_analysis(context)
            
            # Parse response
            try:
                # Try to parse as JSON
                parsed_response = json.loads(ai_response)
                return parsed_response
            except json.JSONDecodeError:
                # If not JSON, return as text
                return {
                    "recommendations": [ai_response],
                    "files_to_add": [],
                    "deployment_plan": [],
                    "tech_stack_analysis": "Анализ выполнен, но ответ не в JSON формате",
                    "priority_actions": []
                }
                
        except Exception as e:
            # Fallback analysis
            return self._get_fallback_analysis(context)
    
    def _get_fallback_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis without AI"""
        recommendations = []
        files_to_add = []
        deployment_plan = []
        
        # Basic recommendations based on detected technologies
        if not context['has_dockerfile']:
            recommendations.append("Добавить Dockerfile для контейнеризации приложения")
            files_to_add.append({
                "name": "Dockerfile",
                "content": "# Add appropriate Dockerfile for your project",
                "description": "Конфигурация Docker контейнера"
            })
        
        if 'python' in context['detected_languages'] and not context['has_requirements']:
            recommendations.append("Добавить requirements.txt для Python зависимостей")
            files_to_add.append({
                "name": "requirements.txt",
                "content": "# Add your Python dependencies here",
                "description": "Python зависимости"
            })
        
        if 'node' in context['detected_languages'] and not context['has_package_json']:
            recommendations.append("Добавить package.json для Node.js зависимостей")
            files_to_add.append({
                "name": "package.json",
                "content": '{"name": "your-project", "version": "1.0.0", "dependencies": {}}',
                "description": "Node.js конфигурация"
            })
        
        # Always recommend CI/CD
        recommendations.append("Настроить CI/CD пайплайн с GitHub Actions")
        files_to_add.append({
            "name": ".github/workflows/ci.yml",
            "content": "# Add GitHub Actions workflow",
            "description": "CI/CD пайплайн"
        })
        
        deployment_plan = [
            "1. Настроить автоматическую сборку",
            "2. Добавить тестирование",
            "3. Настроить развертывание",
            "4. Добавить мониторинг"
        ]
        
        return {
            "recommendations": recommendations,
            "files_to_add": files_to_add,
            "deployment_plan": deployment_plan,
            "tech_stack_analysis": f"Обнаружены технологии: {', '.join(context['detected_languages'])}",
            "priority_actions": ["Добавить Dockerfile", "Настроить CI/CD"]
        }

# Initialize services
analyzer = GitHubAnalyzer()
deploy_service = DeployService(analyzer.automata_path)

@app.get("/")
async def root():
    return FileResponse("front/index.html")

@app.get("/deploy")
async def deploy_page():
    return FileResponse("front/deploy.html")

@app.post("/analyze")
async def analyze_repo(request: Dict[str, str]):
    """Analyze GitHub repository"""
    github_url = request.get("github_url")
    if not github_url:
        raise HTTPException(status_code=400, detail="GitHub URL is required")
    
    result = await analyzer.analyze_repository(github_url)
    return result

@app.post("/test-server")
async def test_server(server_config: dict):
    """Test SSH connection to server"""
    try:
        result = await deploy_service.test_server_connection(server_config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy")
async def deploy_repository(request: dict):
    """Deploy repository to server"""
    try:
        server_config = request.get("server", {})
        repository = request.get("repository", {})
        
        if not server_config or not repository:
            raise HTTPException(status_code=400, detail="Server config and repository info are required")
        
        async def generate():
            async for log_line in deploy_service.deploy_repository(server_config, repository):
                yield f"data: {json.dumps({'message': log_line})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-deploy")
async def stop_deploy():
    """Stop active deployment"""
    deploy_service.stop_deployment()
    return {"status": "stopped"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
