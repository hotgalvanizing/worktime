"""
从Redmine获取工作时间的工具模块
"""

import requests
from bs4 import BeautifulSoup
from datetime import date
from dataclasses import dataclass


@dataclass
class Settings:
    """用户配置"""
    user_id: str = ""
    cookie: str = ""
    username: str = ""
    password: str = ""


# 全局配置实例
settings = Settings()


def get_work_time(day: str, user_id: str = None) -> str:
    """
    获取指定日期的工作时间

    Args:
        day: 日期字符串，格式如 "2024-01-15"
        user_id: 用户ID/工号，如果为None则使用settings中的user_id

    Returns:
        工作时间字符串
    """
    url = "https://redmine-pa.mxnavi.com/cardinfos"

    # 使用传入的user_id或settings中的user_id
    code = user_id if user_id is not None else settings.user_id

    params = {
        "utf8": "✓",
        "code": code,
        "event_time[]": day,
        "commit": "查询"
    }

    cookies = {
        "_redmine_session": settings.cookie
    }

    # 不跟随重定向
    response = requests.get(
        url,
        params=params,
        cookies=cookies,
        allow_redirects=False
    )

    # 更新cookie
    if "_redmine_session" in response.cookies:
        settings.cookie = response.cookies["_redmine_session"]

    # 解析HTML获取工作时间
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find(id="workreport-table")

    if table:
        tds = table.find_all("td")
        if tds:
            return tds[-1].get_text(strip=True)

    return ""


def login(username: str, password: str) -> bool:
    """
    模拟登录Redmine系统

    Args:
        username: 用户名
        password: 密码

    Returns:
        登录成功返回True，失败返回False
    """
    # 检查用户名密码是否为空
    if not username or not password:
        print("请设置账号密码！")
        return False

    # 清空之前的cookie和user_id
    settings.cookie = ""
    settings.user_id = ""
    settings.username = username
    settings.password = password

    try:
        # 第一步：获取登录页面和CSRF token
        login_url = "https://redmine-pa.mxnavi.com/login"
        response = requests.get(login_url, allow_redirects=False)

        # 获取cookie
        if "_redmine_session" in response.cookies:
            settings.cookie = response.cookies["_redmine_session"]

        # 解析HTML获取CSRF token
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.head.find("meta", attrs={"name": "csrf-token"})
        if csrf_token:
            csrf_token = csrf_token.get("content", "")
        else:
            print("无法获取CSRF token")
            return False

        # 第二步：提交登录表单
        login_data = {
            "utf8": "✓",
            "authenticity_token": csrf_token,
            "back_url": "/cardinfos",
            "username": username,
            "password": password,
            "login": "登录"
        }

        headers = {
            "Cookie": f"_redmine_session={settings.cookie}"
        }

        # 不跟随重定向
        response = requests.post(
            login_url,
            data=login_data,
            headers=headers,
            allow_redirects=False
        )

        # 更新cookie
        if "_redmine_session" in response.cookies:
            settings.cookie = response.cookies["_redmine_session"]

        # 第三步：访问cardinfos页面获取user_id
        cardinfos_url = "https://redmine-pa.mxnavi.com/cardinfos"
        headers = {
            "Cookie": f"_redmine_session={settings.cookie}"
        }

        response = requests.get(cardinfos_url, headers=headers, allow_redirects=False)

        # 解析HTML获取user_id
        soup = BeautifulSoup(response.text, "html.parser")

        # 方法1：从"登录为"链接中提取user_id
        loggedas_div = soup.find("div", id="loggedas")
        if loggedas_div:
            user_link = loggedas_div.find("a")
            if user_link and user_link.get("href"):
                # href格式为"/people/901"，提取数字部分
                href = user_link.get("href")
                user_id = href.split("/")[-1]  # 获取最后一部分数字
                settings.user_id = user_id
                print(f"成功获取user_id: {user_id}")

        # 方法2：备用方法，从任何/people/数字链接中提取
        if not settings.user_id:
            import re
            people_links = soup.find_all("a", href=re.compile(r"/people/\d+"))
            if people_links:
                href = people_links[0].get("href")
                user_id = re.findall(r"/people/(\d+)", href)[0]
                settings.user_id = user_id
                print(f"通过备用方法获取user_id: {user_id}")

        # 更新cookie
        if "_redmine_session" in response.cookies:
            settings.cookie = response.cookies["_redmine_session"]

        if not settings.user_id:
            print("警告：未能获取到user_id")
            return False

        return True

    except Exception as e:
        print(f"登录失败：{str(e)}")
        return False


# 使用示例
if __name__ == "__main__":
    # 方式1：使用登录功能（推荐）
    username = ""  # 替换为你的用户名
    password = ""  # 替换为你的密码

    if login(username, password):
        # 获取今天的工作时间
        today = date.today().strftime("%Y-%m-%d")
        work_time = get_work_time(today)
        print(f"今日工作时间: {work_time}")
    else:
        print("登录失败，请检查用户名密码")
