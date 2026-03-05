"""
Bilibili Cookie 获取脚本
支持两种可靠的方式：
1. 扫码登录（推荐）- 使用手机APP扫描二维码
2. 手动输入 - 从浏览器开发者工具复制Cookie
"""

import json
import os
import sys
import time
import requests

# Bilibili 扫码登录 API
QRCODE_GENERATE_URL = (
    "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
)
QRCODE_POLL_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"

# 通用请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}


def print_qrcode_ascii(url: str) -> None:
    """在终端打印ASCII二维码"""
    try:
        import qrcode

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # 使用Unicode字符打印更清晰的二维码
        matrix = qr.get_matrix()
        for row in matrix:
            line = ""
            for cell in row:
                line += "██" if cell else "  "
            print(line)
        return True
    except ImportError:
        print("提示: 安装 qrcode 库可以显示二维码: pip install qrcode")
        print(f"请在浏览器中打开此链接扫码: {url}")
        return False


def qrcode_login() -> dict | None:
    """
    扫码登录获取Cookie
    返回: cookie字典 或 None（失败时）
    """
    print("\n" + "=" * 60)
    print("【扫码登录】")
    print("=" * 60)

    # 1. 获取二维码
    print("\n正在生成登录二维码...")
    try:
        resp = requests.get(QRCODE_GENERATE_URL, headers=HEADERS, timeout=10)
        data = resp.json()

        if data.get("code") != 0:
            print(f"✗ 生成二维码失败: {data.get('message', '未知错误')}")
            return None

        qrcode_key = data["data"]["qrcode_key"]
        qrcode_url = data["data"]["url"]

    except requests.RequestException as e:
        print(f"✗ 网络错误: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        print(f"✗ 解析响应失败: {e}")
        return None

    # 2. 显示二维码
    print("\n请使用 Bilibili 手机APP 扫描下方二维码：\n")
    print_qrcode_ascii(qrcode_url)
    print("\n等待扫码中... (3分钟内有效)")
    print("-" * 60)

    # 3. 轮询登录状态
    start_time = time.time()
    timeout = 180  # 3分钟

    while time.time() - start_time < timeout:
        try:
            poll_resp = requests.get(
                QRCODE_POLL_URL,
                params={"qrcode_key": qrcode_key},
                headers=HEADERS,
                timeout=10,
            )
            poll_data = poll_resp.json()

            code = poll_data.get("data", {}).get("code", -1)

            if code == 0:
                # 登录成功
                print("\n\n✓ 登录成功！")

                # 从响应URL中提取cookie参数
                refresh_url = poll_data["data"].get("url", "")
                cookies_from_url = {}

                if "?" in refresh_url:
                    params_str = refresh_url.split("?")[1]
                    for param in params_str.split("&"):
                        if "=" in param:
                            key, value = param.split("=", 1)
                            cookies_from_url[key] = value

                # 从Set-Cookie响应头提取cookies
                cookies_from_header = {}
                if poll_resp.cookies:
                    for cookie in poll_resp.cookies:
                        cookies_from_header[cookie.name] = cookie.value

                # 合并所有cookies
                all_cookies = {**cookies_from_url, **cookies_from_header}

                # 验证必要字段
                if "SESSDATA" in all_cookies and "DedeUserID" in all_cookies:
                    return all_cookies
                else:
                    print("✗ Cookie不完整，缺少必要字段")
                    print(f"  获取到的字段: {list(all_cookies.keys())}")
                    return None

            elif code == 86038:
                # 二维码已过期
                print("\n\n✗ 二维码已过期，请重新运行脚本")
                return None

            elif code == 86090:
                # 已扫码，等待确认
                remaining = int(timeout - (time.time() - start_time))
                print(
                    f"\r✓ 已扫码，请在手机上确认登录... ({remaining}s)",
                    end="",
                    flush=True,
                )

            elif code == 86101:
                # 未扫码
                remaining = int(timeout - (time.time() - start_time))
                print(f"\r⏳ 等待扫码... ({remaining}s)", end="", flush=True)

            time.sleep(2)

        except requests.RequestException as e:
            print(f"\n✗ 网络错误: {e}")
            return None

    print("\n\n✗ 超时：3分钟内未完成登录")
    return None


def manual_input() -> dict | None:
    """
    手动输入Cookie
    返回: cookie字典 或 None（失败时）
    """
    print("\n" + "=" * 60)
    print("【手动输入 Cookie】")
    print("=" * 60)
    print("""
操作步骤：
1. 打开浏览器，访问 https://www.bilibili.com 并登录
2. 按 F12 打开开发者工具
3. 切换到「Network」标签
4. 刷新页面，点击任意请求
5. 在「Headers」中找到「Cookie」字段
6. 复制整个Cookie字符串
7. 确保字符串为单行，没有换行符，一个简单的处理方法是将其粘贴到浏览器顶部的搜索栏中（不用搜索），再复制
""")

    print("请粘贴Cookie字符串 (输入 'q' 返回)：")
    cookie_input = input().strip()

    if cookie_input.lower() == "q":
        return None

    # 解析Cookie字符串
    cookie_dict = {}
    for item in cookie_input.replace("\n", "").split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            cookie_dict[key.strip()] = value.strip()

    # 验证必要字段
    required = ["SESSDATA", "DedeUserID"]
    missing = [f for f in required if f not in cookie_dict]

    if missing:
        print(f"\n✗ Cookie缺少必要字段: {', '.join(missing)}")
        print("  请确保已登录Bilibili并复制完整的Cookie")
        return None

    print("\n✓ Cookie格式正确！")
    return cookie_dict


def verify_cookie(cookie_dict: dict) -> bool:
    """验证Cookie是否有效"""
    print("\n正在验证Cookie...")

    cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
    headers = {**HEADERS, "Cookie": cookie_str}

    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/nav", headers=headers, timeout=10
        )
        data = resp.json()

        if data.get("code") == 0 and data.get("data", {}).get("isLogin"):
            uname = data["data"].get("uname", "未知")
            mid = data["data"].get("mid", "未知")
            print(f"✓ Cookie有效！")
            print(f"  用户名: {uname}")
            print(f"  UID: {mid}")
            return True
        else:
            print(f"✗ Cookie无效或已过期")
            return False

    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False


def save_config(cookie_dict: dict) -> bool:
    """保存配置到config.json"""
    uid = cookie_dict.get("DedeUserID", "")
    if not uid:
        print("✗ 无法获取用户UID")
        return False

    cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

    config = {
        "uid": uid,
        "cookie": cookie_str,
        "settings": {
            "max_workers_crawl": 3,
            "max_workers_image": 10,
            "page_delay": 0.3,
            "image_retry": 3,
            "backup_keep_count": 5,
            "enable_incremental": True,
            "csv_export": True
        }
    }

    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        print("\n" + "=" * 60)
        print("✓ 配置已保存到 config.json")
        print("=" * 60)
        print(f"  UID: {uid}")
        print(f"  现在可以运行 python main.py 开始爬取了！")
        return True

    except Exception as e:
        print(f"✗ 保存配置失败: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("       Bilibili Cookie 获取工具")
    print("=" * 60)

    while True:
        print("""
请选择获取方式：
  1. 扫码登录（推荐，需要手机APP）
  2. 手动输入Cookie
  q. 退出
""")
        choice = input("请输入选项 (1/2/q): ").strip().lower()

        cookie_dict = None

        if choice == "1":
            cookie_dict = qrcode_login()
        elif choice == "2":
            cookie_dict = manual_input()
        elif choice == "q":
            print("\n再见！")
            sys.exit(0)
        else:
            print("\n无效选项，请重新选择")
            continue

        if cookie_dict:
            if verify_cookie(cookie_dict):
                save_config(cookie_dict)
                break
            else:
                print("\n获取到的Cookie无效，请重试")
        else:
            print("\n获取Cookie失败，请重试或选择其他方式")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
