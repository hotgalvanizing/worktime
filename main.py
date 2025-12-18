"""
FastAPI接口：获取今日工作时间
"""

from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

from get_work_time import login, get_work_time, settings

app = FastAPI(title="工作时间查询接口")


class LoginRequest(BaseModel):
    username: str
    password: str


class WorkTimeResponse(BaseModel):
    date: str
    work_time: str


@app.post("/work-time", response_model=WorkTimeResponse)
def get_today_work_time(request: LoginRequest):
    """
    获取今日工作时间

    - **username**: Redmine用户名
    - **password**: Redmine密码
    """
    if not login(request.username, request.password):
        raise HTTPException(status_code=401, detail="登录失败，请检查用户名密码")

    today = date.today().strftime("%Y-%m-%d")
    print(f"查询日期: {today}")
    print(f"用户ID: {settings.user_id}")
    work_time = get_work_time(today, settings.user_id)
    print(f"获取到的工作时间: {work_time}")

    return WorkTimeResponse(date=today, work_time=work_time)


# 在所有路由定义之后挂载静态文件
# 这样API路由会优先匹配，静态文件作为后备
app.mount("/", StaticFiles(directory=".", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)