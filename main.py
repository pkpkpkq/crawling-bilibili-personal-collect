import json
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from concurrent import futures
from viewing import view
import requests
import math
import sys
import shutil

# --- Core Functions ---

def ProcessRawData(RawData):
    NewData = {}
    for i in RawData.values():
        media = {
            "id": i['id'], "BV": i['bv_id'], "是否失效": False,
            "up主": {"ID": i['upper']['mid'], "昵称": i['upper']['name'], "头像": i['upper']['face']},
            "视频信息": {"标题": i['title'], "封面": i['cover'], "简介": i['intro'], "时长": time.strftime("%H:%M:%S", time.gmtime(i['duration']))},
            "观众数据": {"播放量": i['cnt_info']['play'], "收藏量": i['cnt_info']['collect'], "弹幕数量": i['cnt_info']['danmaku']},
            "三个时间": {"上传时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['ctime'])), "发布时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['pubtime'])), "收藏时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['fav_time']))}
        }
        NewData[str(media['id'])] = media
    return NewData

def CompareLastTime(ReadPath, NewData):
    if not os.path.exists(ReadPath):
        return NewData
    try:
        with open(ReadPath, 'r', encoding='utf-8') as f:
            OldData = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.warning(f"读取旧数据文件失败 {ReadPath}: {e}，将使用新数据")
        return NewData
    
    # 视频被删除，则保留上次的数据，并且标记
    for new_key, i in list(NewData.items()):
        # 统一使用字符串键查询OldData
        str_id = str(i['id'])
        if i['视频信息']['标题'] == "已失效视频" and str_id in OldData.keys():
            logging.info(f"{OldData[str_id]['视频信息']['标题']} 已失效")
            OldData[str_id]['是否失效'] = True
            NewData[str_id] = OldData[str_id]

    # 自己取消收藏，标记并记录取消时间
    for old_key, i in list(OldData.items()):
        str_id = str(i['id'])
        if str_id not in NewData.keys():
            logging.info(f"{i['视频信息']['标题']} 已取消收藏")
            i['是否取消了收藏'] = True
            i['取消收藏时间'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            NewData[str_id] = i

    return NewData

# --- Bilibili API Functions ---

def GetFavoriteID(WritePath, uid, headers):
    url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all'
    params = {'up_mid': uid, 'jsonp': 'jsonp'}
    try:
        response = requests.get(url=url, params=params, headers=headers)
        response.raise_for_status()
        assign = response.json()
        if assign.get('code') != 0:
            logging.error(f"获取收藏夹列表失败: {assign.get('message', 'API返回错误')}")
            return False
        with open(os.path.join(WritePath, '收藏夹id.json'), 'w', encoding='utf-8') as fp:
            json.dump(assign, fp, ensure_ascii=False)
        logging.info('收藏夹id爬取成功')
        return True
    except requests.RequestException as e:
        logging.error(f"请求收藏夹ID API时发生网络错误: {e}")
        return False


def verify_cookie(headers):
    """验证Cookie是否有效"""
    try:
        response = requests.get('https://api.bilibili.com/x/web-interface/nav', 
                               headers=headers, timeout=5)
        data = response.json()
        return data.get('code') == 0
    except Exception as e:
        logging.warning(f"Cookie验证失败: {e}")
        return False

def GetFollowingUPs(uid, WritePath, headers):
    logging.info("开始爬取关注的UP主列表...")
    url = 'https://api.bilibili.com/x/relation/followings'
    params = {'vmid': uid, 'ps': 50, 'pn': 1, 'order': 'desc', 'order_type': 'attention', 'jsonp': 'jsonp'}
    all_following_ups = []
    consecutive_empty_pages = 0  # 连续空页计数
    max_consecutive_empty = 2    # 连续2页为空则停止
    while True:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 0:
                following_list = data.get('data', {}).get('list', [])
                if not following_list:
                    consecutive_empty_pages += 1
                    logging.warning(f"关注列表第 {params['pn']} 页为空（连续空页: {consecutive_empty_pages}/{max_consecutive_empty}）")
                    if consecutive_empty_pages >= max_consecutive_empty:
                        logging.info("已获取所有关注的UP主。")
                        break
                else:
                    consecutive_empty_pages = 0  # 重置计数器
                    for up in following_list:
                        all_following_ups.append({"ID": up['mid'], "昵称": up['uname'], "头像": up['face']})
                logging.info(f"成功爬取第 {params['pn']} 页关注列表，已获取 {len(all_following_ups)} 位UP主。")
                params['pn'] += 1
                time.sleep(1)
            else:
                logging.error(f"获取关注列表时出错: {data.get('message', '未知API错误')}")
                break
        except requests.Timeout:
            logging.error(f"第 {params['pn']} 页关注列表请求超时")
            break
        except requests.RequestException as e:
            logging.error(f"请求关注列表API时发生网络错误: {e}")
            break
        except Exception as e:
            logging.error(f"处理关注列表数据时发生未知错误: {e}")
            break
    with open(os.path.join(WritePath, '关注UP列表.json'), 'w', encoding='utf-8') as f:
        json.dump(all_following_ups, f, ensure_ascii=False, indent=4)
    logging.info(f"关注的UP主列表爬取完成，共 {len(all_following_ups)} 位。")

def GetOneFavorite(Media_Id, MaxPage, headers):
    url = 'https://api.bilibili.com/x/v3/fav/resource/list'
    params = {'ps': 20, 'keyword': '', 'order': 'mtime', 'type': 0, 'tid': 0, 'platform': 'web', 'jsonp': 'jsonp', 'pn': 1, 'media_id': Media_Id}
    data = {}
    for pn in range(1, MaxPage):
        params['pn'] = pn
        logging.info(f"正在爬取第 {pn} 页")
        try:
            response = requests.get(url=url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            json_data = response.json()
            if json_data.get('code') != 0:
                logging.error(f"收藏夹 {Media_Id} 第 {pn} 页API返回错误: {json_data.get('message', '未知错误')}")
                break
            medias_list = json_data.get('data', {}).get('medias', [])
            if not medias_list:
                break
            for i in medias_list:
                data[str(i['id'])] = i
        except requests.Timeout:
            logging.error(f"收藏夹 {Media_Id} 第 {pn} 页请求超时")
            break
        except requests.RequestException as e:
            logging.error(f"收藏夹 {Media_Id} 第 {pn} 页网络错误: {e}")
            break
        except json.JSONDecodeError as e:
            logging.error(f"收藏夹 {Media_Id} 第 {pn} 页JSON解析错误: {e}")
            break
    return data

def GetALLFavorite(WritePath, headers, BackupPath='收藏夹信息/'):
    id_file = os.path.join(WritePath, '收藏夹id.json')
    with open(id_file, 'r', encoding='utf-8') as fp:
        file = json.load(fp)
    ID_list = file.get('data', {}).get('list', [])
    for i in ID_list:
        logging.info(f"爬取中...当前正在爬取 {i['title']}")
        filename = os.path.join(WritePath, i['title'] + '.json')
        # 从备份路径读取历史数据进行对比
        history_file = os.path.join(BackupPath, i['title'] + '.json')
        data = GetOneFavorite(i['id'], math.ceil(i['media_count'] / 20) + 1, headers)
        a_fav_data = CompareLastTime(history_file, ProcessRawData(data))
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(a_fav_data, f, ensure_ascii=False, indent=4)
    os.remove(id_file)
    logging.info('所有收藏夹爬取完毕！！！')

# --- Image Fetching ---

def SetPhotoURL(ReadPath):
    file_name_list = [f for f in os.listdir(ReadPath) if f.endswith('.json') and f != '关注UP列表.json']
    Cover_dict = {}
    Face_dict = {}
    for i in file_name_list:
        cover_url = {}
        try:
            with open(os.path.join(ReadPath, i), 'r', encoding='utf-8') as f1:
                data = json.load(f1)
            for j in data.values():
                if j['是否失效']:
                    cover_url['已失效视频'] = j['视频信息']['封面']
                else:
                    cover_url[j['BV']] = j['视频信息']['封面']
                Face_dict[j['up主']['ID']] = j['up主']['头像']
            Cover_dict[i.split('.')[0]] = cover_url
        except (json.JSONDecodeError, FileNotFoundError):
            logging.warning(f"读取或解析收藏夹JSON文件 {i} 失败，已跳过。")
    following_list_path = os.path.join(ReadPath, '关注UP列表.json')
    if os.path.exists(following_list_path):
        try:
            with open(following_list_path, 'r', encoding='utf-8') as f:
                following_ups = json.load(f)
            for up in following_ups:
                if up['ID'] not in Face_dict:
                    Face_dict[up['ID']] = up['头像']
        except (json.JSONDecodeError, FileNotFoundError):
            logging.warning("读取或解析关注UP列表JSON文件失败，已跳过。")
    temp_dir = os.path.join('.', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    cover_url_path = os.path.join(temp_dir, '视频封面url.json')
    face_url_path = os.path.join(temp_dir, 'up头像url.json')
    with open(cover_url_path, 'w', encoding='utf-8') as fp:
        json.dump(Cover_dict, fp, ensure_ascii=False, indent=4)
    with open(face_url_path, 'w', encoding='utf-8') as fp:
        json.dump(Face_dict, fp, ensure_ascii=False, indent=4)

def fetch_image(url, path, identifier, log_prefix):
    if not (url and isinstance(url, str) and url.startswith(('http://', 'https://'))):
        return
    if os.path.exists(path):
        return
    for attempt in range(3):
        try:
            response = requests.get(url, headers={'Referer': 'https://www.bilibili.com/'}, timeout=10)
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(response.content)
                return
        except Exception:
            pass
        if attempt < 2:
            time.sleep(2 ** attempt)

def GetImages(temp_dir):
    cover_url_file = os.path.join(temp_dir, '视频封面url.json')
    face_url_file = os.path.join(temp_dir, 'up头像url.json')
    with open(cover_url_file, 'r', encoding='utf-8') as fp:
        cover_urls = json.load(fp)
    with open(face_url_file, 'r', encoding='utf-8') as fp:
        face_urls = json.load(fp)
    
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for fav_name, videos in cover_urls.items():
            cover_path_dir = os.path.join('html_report', '视频封面', fav_name)
            os.makedirs(cover_path_dir, exist_ok=True)
            for bv, url in videos.items():
                cover_path = os.path.join(cover_path_dir, f'{bv}.jpg')
                executor.submit(fetch_image, url, cover_path, bv, "bv")

        logging.info("开始爬取所有UP主头像...")
        for mid, url in face_urls.items():
            face_path = os.path.join('html_report', 'up头像', f'{mid}.jpg')
            executor.submit(fetch_image, url, face_path, mid, "mid")
    logging.info("所有图片爬取完成。")


# --- Main Execution ---

if __name__ == "__main__":
    # 配置日志同时输出到文件和控制台
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    
    # 文件处理器
    file_handler = logging.FileHandler('bilibili_crawler.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 1. 读取配置文件
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        UID = config.get("uid")
        COOKIE = config.get("cookie")
        if not COOKIE:
            COOKIE = "_uuid=F500E27C-018D-CC3F-17E8-C64812E174DA08613infoc; buvid3=475B7DAC-0579-421B-85B7-07A4076090B734771infoc; buvid_fp=475B7DAC-0579-421B-85B7-07A4076090B734771infoc; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(k|k)~~RkkJ0J'uYk|YumRkm; fingerprint3=c1d980f375c848a729ebdd130960a847; CURRENT_QUALITY=112; LIVE_BUVID=AUTO9716210898194009; fingerprint_s=be57440a1cba44ed342ad526646463d4; bp_t_offset_51541144=529073781132033226; bp_video_offset_51541144=529330083309673464; bp_t_offset_289920431=529693188424888145; fingerprint=a43248e91a776fba5e92af41d1a900e0; buvid_fp_plain=95AEE299-5E58-4AA1-92EF-CFE2BE6C6243184999infoc; SESSDATA=41ff3c64%2C1637735786%2Cff017%2A51; bili_jct=c0a63b68e972a8d1acc44a3718075b58; DedeUserID=289920431; DedeUserID__ckMd5=c43d13bc962635fe; sid=bvgle9dv; PVID=3; bp_video_offset_289920431=529757320878990660; bfe_id=5db70a86bd1cbe8a88817507134f7bb5"
            logging.warning("配置文件中缺少 'cookie'，已使用默认Cookie，将无法爬取关注的up列表和未公开内容。")
        if not UID:
            raise ValueError("配置文件中缺少 'uid' ")
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"配置文件错误: {e}")
        logging.error("请先正确运行 getcookie.py 来生成有效的 config.json 文件，或者手动创建它。")
        sys.exit(1)

    # 2. 设置通用请求头
    base_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Referer': 'https://www.bilibili.com/',
        'cookie': COOKIE
    }
    
    # 验证Cookie有效性
    if not verify_cookie(base_headers):
        logging.warning("Cookie可能已过期，某些功能（如爬取关注列表）可能无法正常工作")

    # 3. 设置文件夹路径并执行带有安全措施的爬取流程
    main_info_path = '收藏夹信息/'
    temp_info_path = '收藏夹信息_temp/'
    backup_info_path = '收藏夹信息_backup/'
    os.makedirs(main_info_path, exist_ok=True)
    if os.path.exists(temp_info_path):
        shutil.rmtree(temp_info_path)
    os.makedirs(temp_info_path, exist_ok=True)
    if os.path.exists(backup_info_path):
        shutil.rmtree(backup_info_path)

    time_list = []
    crawling_successful = False
    try:
        STime = time.perf_counter()
        if not GetFavoriteID(temp_info_path, UID, base_headers):
            raise Exception("获取收藏夹列表失败，终止爬取。")
        
        GetFollowingUPs(UID, temp_info_path, base_headers)
        GetALLFavorite(temp_info_path, base_headers)
        
        temp_dir = os.path.join('.', 'temp')
        SetPhotoURL(temp_info_path)
        GetImages(temp_dir)
        
        ETime = time.perf_counter()
        time_list.append(time.strftime("%M:%S", time.gmtime(ETime - STime)))
        crawling_successful = True
        
    except Exception as e:
        logging.error(f"爬取主流程发生错误: {e}", exc_info=True)
        
    finally:
        if crawling_successful:
            logging.info("爬取成功，正在更新数据...")
            try:
                if os.path.exists(main_info_path):
                    timestamp = time.strftime('%Y%m%d_%H%M%S')
                    backup_with_time = f'{backup_info_path[:-1]}_{timestamp}/'
                    os.rename(main_info_path, backup_with_time)
                    logging.info(f"旧数据备份至: {backup_with_time}")
                os.rename(temp_info_path, main_info_path)
                logging.info("数据更新完毕。")
            except OSError as e:
                logging.error(f"更新数据失败: {e}")
                if os.path.exists(temp_info_path):
                    shutil.rmtree(temp_info_path)
        else:
            logging.error("爬取失败或被中断，保留原始数据，临时文件已删除。")
            if os.path.exists(temp_info_path):
                shutil.rmtree(temp_info_path)

    # 4. 生成HTML报告
    if crawling_successful:
        STime = time.perf_counter()
        try:
            view(main_info_path, 'html_report')
            ETime = time.perf_counter()
            time_list.append(time.strftime("%M:%S", time.gmtime(ETime - STime)))
            logging.info(f"执行爬取代码所用时间：{time_list[0]}")
            logging.info(f"生成HTML报告所用时间: {time_list[1]}")
        except Exception as e:
            logging.error(f"生成HTML报告时发生错误: {e}", exc_info=True)
    else:
        logging.info("由于爬取失败，跳过HTML报告生成。")
