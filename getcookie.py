import browser_cookie3
import json
import os

def get_bilibili_cookies():
    """
    Tries to get Bilibili cookies from all available browsers.
    """
    try:
        # Load cookies from all supported browsers
        cj = browser_cookie3.load(domain_name='.bilibili.com')
        
        cookie_dict = {}
        for cookie in cj:
            cookie_dict[cookie.name] = cookie.value
        
        # Check for essential cookies
        if 'SESSDATA' in cookie_dict and 'bili_jct' in cookie_dict:
            print("成功从浏览器中找到Bilibili Cookie。")
            return cookie_dict, cj
        else:
            print("错误：在浏览器中找到了B站cookie，但缺少SESSDATA或bili_jct等关键信息。")
            print("请确认您已经在浏览器中登录了Bilibili。")
            return None, None
            
    except Exception as e:
        print(f"自动获取Cookie时发生错误: {e}")
        print("未能从任何浏览器中找到Bilibili Cookie。")
        print("请尝试以下步骤之一：")
        print("1. 确保您已在系统上安装了受支持的浏览器 (Chrome, Firefox, Edge, etc.) 并且已经登录Bilibili。")
        print("2. 手动在`config.json`文件中配置cookie。")
        return None, None

def create_config_from_cookies(cookie_dict, cj):
    """
    Creates a config.json file from the extracted cookie dictionary.
    """
    if not cookie_dict:
        return

    # The DedeUserID is the user's UID
    uid = cookie_dict.get('DedeUserID', '')
    if not uid:
        print("错误：无法从Cookie中找到用户UID (DedeUserID)。")
        return
        
    # Format the cookie string for use in headers
    cookie_string = '; '.join([f'{c.name}={c.value}' for c in cj])

    config_data = {
        "uid": uid,
        "cookie": cookie_string
    }

    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        print("已成功创建/更新 config.json 文件。")
        print(f"用户UID: {uid}")
        print("现在您可以运行 main.py 脚本了。")
    except Exception as e:
        print(f"写入config.json时发生错误: {e}")

if __name__ == '__main__':
    print("正在尝试自动获取Bilibili登录信息...")
    bili_cookies, full_cookie_jar = get_bilibili_cookies()
    if bili_cookies and full_cookie_jar:
        create_config_from_cookies(bili_cookies, full_cookie_jar)
