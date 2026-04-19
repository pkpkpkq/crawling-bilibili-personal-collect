"""
Bilibili Cookie 获取脚本
支持两种可靠的方式：
1. 扫码登录（推荐）- 使用手机APP扫描二维码
2. 手动输入 - 从浏览器开发者工具复制Cookie
"""

import sys
from typing import Optional

from app.services.auth_service import (
    create_qrcode_login_session,
    parse_manual_cookie_input,
    poll_qrcode_login_session,
    serialize_cookie_dict,
    verify_cookie_dict,
)
from app.services.config_service import save_config as save_config_service


def print_qrcode_ascii(url: str) -> bool:
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


def qrcode_login() -> Optional[dict]:
    """扫码登录获取Cookie"""
    print("\n" + "=" * 60)
    print("【扫码登录】")
    print("=" * 60)

    print("\n正在生成登录二维码...")
    create_result = create_qrcode_login_session()
    if not create_result.get("success"):
        print(f"✗ {create_result.get('error', '生成二维码失败')}")
        return None

    qrcode_key = create_result["qrcode_key"]
    qrcode_url = create_result["qrcode_url"]

    print("\n请使用 Bilibili 手机APP 扫描下方二维码：\n")
    print_qrcode_ascii(qrcode_url)
    print("\n等待扫码中... (3分钟内有效)")
    print("-" * 60)

    def _status_callback(status: dict) -> None:
        code = status.get("code")
        remaining = status.get("remaining", 0)
        if code == 86090:
            print(
                f"\r✓ 已扫码，请在手机上确认登录... ({remaining}s)",
                end="",
                flush=True,
            )
        elif code == 86101:
            print(f"\r⏳ 等待扫码... ({remaining}s)", end="", flush=True)

    poll_result = poll_qrcode_login_session(
        qrcode_key,
        timeout_seconds=180,
        poll_interval_seconds=2,
        request_timeout=10,
        status_callback=_status_callback,
    )

    if not poll_result.get("success"):
        status = poll_result.get("status")
        if status == "expired":
            print("\n\n✗ 二维码已过期，请重新运行脚本")
        elif status == "timeout":
            print("\n\n✗ 超时：3分钟内未完成登录")
        else:
            print(f"\n\n✗ {poll_result.get('error', '扫码登录失败')}")
            if status == "incomplete_cookie":
                fields = poll_result.get("cookie_dict", {}).keys()
                print(f"  获取到的字段: {list(fields)}")
        return None

    print("\n\n✓ 登录成功！")
    return poll_result.get("cookie_dict")


def manual_input() -> Optional[dict]:
    """手动输入Cookie"""
    print("\n" + "=" * 60)
    print("【手动输入 Cookie】")
    print("=" * 60)
    print(
        """
操作步骤：
1. 打开浏览器，访问 https://www.bilibili.com 并登录
2. 按 F12 打开开发者工具
3. 切换到「Network」标签
4. 刷新页面，点击任意请求
5. 在「Headers」中找到「Cookie」字段
6. 复制整个Cookie字符串
7. 确保字符串为单行，没有换行符，一个简单的处理方法是将其粘贴到浏览器顶部的搜索栏中（不用搜索），再复制
"""
    )

    print("请粘贴Cookie字符串 (输入 'q' 返回)：")
    cookie_input = input().strip()

    if cookie_input.lower() == "q":
        return None

    parse_result = parse_manual_cookie_input(cookie_input)
    if not parse_result.get("success"):
        missing = parse_result.get("missing_fields", [])
        print(f"\n✗ Cookie缺少必要字段: {', '.join(missing)}")
        print("  请确保已登录Bilibili并复制完整的Cookie")
        return None

    print("\n✓ Cookie格式正确！")
    return parse_result.get("cookie_dict")


def verify_cookie(cookie_dict: dict) -> bool:
    """验证Cookie是否有效"""
    print("\n正在验证Cookie...")
    result = verify_cookie_dict(cookie_dict, timeout=10, require_login=True)

    if result.valid:
        uname = result.uname or "未知"
        mid = result.mid or "未知"
        print("✓ Cookie有效！")
        print(f"  用户名: {uname}")
        print(f"  UID: {mid}")
        return True

    if result.error:
        print(f"✗ 验证失败: {result.error}")
    else:
        print("✗ Cookie无效或已过期")
    return False


def save_config(cookie_dict: dict) -> bool:
    """保存配置到config.json"""
    uid = cookie_dict.get("DedeUserID", "")
    if not uid:
        print("✗ 无法获取用户UID")
        return False

    cookie_str = serialize_cookie_dict(cookie_dict)

    try:
        save_config_service(uid=uid, cookie=cookie_str)
        print("\n" + "=" * 60)
        print("✓ 配置已保存到 config.json")
        print("=" * 60)
        print(f"  UID: {uid}")
        print("  现在可以运行 python main.py 开始爬取了！")
        return True
    except Exception as e:
        print(f"✗ 保存配置失败: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("       Bilibili Cookie 获取工具")
    print("=" * 60)

    while True:
        print(
            """
请选择获取方式：
  1. 扫码登录（推荐，需要手机APP）
  2. 手动输入Cookie
  q. 退出
"""
        )
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
