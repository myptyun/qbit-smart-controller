from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from app.api.config import router as config_router
from app.api.lucky import router as lucky_router
from app.api.qbit import router as qbit_router
from app.core.config_manager import ConfigManager
from app.core.lucky_monitor import LuckyMonitor
from app.core.qbit_manager import QBittorrentManager

# 全局变量
config_manager = None
lucky_monitor = None
qbit_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    global config_manager, lucky_monitor, qbit_manager
    config_manager = ConfigManager()
    lucky_monitor = LuckyMonitor(config_manager)
    qbit_manager = QBittorrentManager(config_manager)
    yield
    # 关闭时清理
    await lucky_monitor.close()
    await qbit_manager.close_all_sessions()

app = FastAPI(
    title="智能 qBittorrent 限速控制器",
    description="基于Lucky设备状态的智能限速控制",
    version="1.0.0",
    lifespan=lifespan
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# 注册API路由
app.include_router(config_router)
app.include_router(lucky_router)
app.include_router(qbit_router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """主页面"""
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )