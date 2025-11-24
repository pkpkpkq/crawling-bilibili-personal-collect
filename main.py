import json
import os
import time
import logging
from concurrent import futures
from viewing import view
import requests
import math


# 处理原始数据,去掉一些无用信息，让数据更整齐
def ProcessRawData(RawData):
    NewData = {}
    for i in RawData.values():
        media = {
            "id": i['id'],
            "BV": i['bv_id'],
            "是否失效": False,
            "up主": {
                "ID": i['upper']['mid'],
                "昵称": i['upper']['name'],
                "头像": i['upper']['face']
            },
            "视频信息": {
                "标题": i['title'],
                "封面": i['cover'],
                "简介": i['intro'],
                "时长": time.strftime("%H:%M:%S", time.gmtime(i['duration']))
            },
            "观众数据": {
                "播放量": i['cnt_info']['play'],
                "收藏量": i['cnt_info']['collect'],
                "弹幕数量": i['cnt_info']['danmaku']
            },
            "三个时间": {
                "上传时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['ctime'])),
                "发布时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['pubtime'])),
                "收藏时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['fav_time']))
            }
        }
        NewData[media['id']] = media
    return NewData


# 与上一次爬取对比，对于被删除的和自己取消收藏的视频,予以不同的标记
def CompareLastTime(ReadPath, NewData):
    if not os.path.exists(ReadPath):
        return NewData
    with open(ReadPath, 'r', encoding='utf-8') as f:
        OldData = json.load(f)
    # 视频被删除，则保留上次的数据，并且标记
    for i in list(NewData.values()):
        if i['视频信息']['标题'] == "已失效视频" and str(i['id']) in OldData.keys():
            logging.info(f"{OldData[str(i['id'])]['视频信息']['标题']} 已失效")
            OldData[str(i['id'])]['是否失效'] = True
            NewData[str(i['id'])] = OldData[str(i['id'])]

    # 自己取消收藏，标记
    for i in list(OldData.values()):
        if i['id'] not in NewData.keys():
            logging.info(f"{i['视频信息']['标题']} 已取消收藏")
            OldData[str(i['id'])]['是否取消了收藏'] = True
            NewData[str(i['id'])] = OldData[str(i['id'])]

    return NewData


# 爬取收藏夹的ID
def GetFavoriteID(WritePath, UID):
    # 请求头
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Referer': 'https://www.bilibili.com/'
    }
    url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all'
    params = {
        'up_mid': UID,  # 自己账号的UID
        'jsonp': 'jsonp',
    }
    response = requests.get(url=url, params=params, headers=headers)
    assign = response.json()

    with open(WritePath + '收藏夹id.json', 'w', encoding='utf-8') as fp:
        json.dump(assign, fp, ensure_ascii=False)
    logging.info('收藏夹id爬取成功')


# 爬取一个收藏夹信息，Media_Id代表收藏夹，MaxPage代表收藏夹的页数
def GetOneFavorite(Media_Id, MaxPage):
    # 爬虫的参数，其中params里的pn（页数）会随着遍历的改变而改变
    url = 'https://api.bilibili.com/x/v3/fav/resource/list'
    params = {
        'ps': 20,
        'keyword': '',
        'order': 'mtime',
        'type': 0,
        'tid': 0,
        'platform': 'web',
        'jsonp': 'jsonp',
        'pn': 1,
        'media_id': Media_Id
    }
    headers = {
        'authority': 'api.bilibili.com',
        'method': 'GET',
        'path': '/x/v3/fav/resource/list?media_id=309076131&pn=1&ps=20&keyword=&order=mtime&type=0&tid=0&platform=web&jsonp=jsonp',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        # 'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'cookie': "_uuid=F500E27C-018D-CC3F-17E8-C64812E174DA08613infoc; buvid3=475B7DAC-0579-421B-85B7-07A4076090B734771infoc; buvid_fp=475B7DAC-0579-421B-85B7-07A4076090B734771infoc; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(k|k)~~RkkJ0J'uYk|YumRkm; fingerprint3=c1d980f375c848a729ebdd130960a847; CURRENT_QUALITY=112; LIVE_BUVID=AUTO9716210898194009; fingerprint_s=be57440a1cba44ed342ad526646463d4; bp_t_offset_51541144=529073781132033226; bp_video_offset_51541144=529330083309673464; bp_t_offset_289920431=529693188424888145; fingerprint=a43248e91a776fba5e92af41d1a900e0; buvid_fp_plain=95AEE299-5E58-4AA1-92EF-CFE2BE6C6243184999infoc; SESSDATA=41ff3c64%2C1637735786%2Cff017%2A51; bili_jct=c0a63b68e972a8d1acc44a3718075b58; DedeUserID=289920431; DedeUserID__ckMd5=c43d13bc962635fe; sid=bvgle9dv; PVID=3; bp_video_offset_289920431=529757320878990660; bfe_id=5db70a86bd1cbe8a88817507134f7bb5",
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    }

    data = {}
    # 遍历爬取一个收藏夹的不同页数，然后合并到一个字典里
    for pn in range(1, MaxPage):
        params['pn'] = pn
        logging.info(f"正在爬取第 {pn} 页")

        response = requests.get(url=url, params=params, headers=headers).json()
        medias_list = response['data']['medias']
        # 将不同页数合并到字典里
        for i in medias_list:
            data[i['id']] = i
    return data


# 爬取全部收藏夹信息
def GetALLFavorite(WritePath):
    # 打开文件，获取之前爬取到的收藏夹id和收藏夹页数
    with open(WritePath + '收藏夹id.json', 'r', encoding='utf-8') as fp:
        file = json.load(fp)
    ID_list = file['data']['list']

    # 遍历所有收藏夹，爬取所有收藏夹
    for i in ID_list:
        logging.info(f"爬取中...当前正在爬取 {i['title']}")
        filename = os.path.join(WritePath, i['title'] + '.json')

        # 获得一个收藏夹信息，经过处理后一个json文件中
        data = GetOneFavorite(i['id'], math.ceil(i['media_count'] / 20) + 1)
        a_fav_data = CompareLastTime(filename, ProcessRawData(data))
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(a_fav_data, f, ensure_ascii=False, indent=4)

    os.remove(WritePath + '收藏夹id.json')
    logging.info('所有收藏夹爬取完毕！！！')


def SetPhotoURL(ReadPath):
    file_name_list = os.listdir(ReadPath)
    Cover_dict = {}
    Face_dict = {}
    for i in file_name_list:
        cover_url = {}  # 视频封面按收藏夹分类
        with open(os.path.join(ReadPath, i), 'r', encoding='utf-8') as f1:
            data = json.load(f1)
        for j in data.values():
            if j['是否失效']:
                cover_url['已失效视频'] = j['视频信息']['封面']
                logging.info(f"{j['视频信息']['标题']} 已失效")
            else:
                cover_url[j['BV']] = j['视频信息']['封面']
            Face_dict[j['up主']['ID']] = j['up主']['头像']

        Cover_dict[i.split('.')[0]] = cover_url
    with open('视频封面url.json', 'w', encoding='utf-8') as fp:
        json.dump(Cover_dict, fp, ensure_ascii=False, indent=4)
    with open('up头像url.json', 'w', encoding='utf-8') as fp:
        json.dump(Face_dict, fp, ensure_ascii=False, indent=4)


# 爬取视频封面
def GetCover(PhotoURL_filename):
    with open(PhotoURL_filename, 'r', encoding='utf-8') as fp:
        PhotoURL_dict = json.load(fp)

    MaxCount = sum(len(v) for v in PhotoURL_dict.values())
    current_count = 0
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Referer': 'https://www.bilibili.com/'
    }

    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_info = {}

        for fav_name, videos in PhotoURL_dict.items():
            Cover_Path = os.path.join('视频封面', fav_name)
            if not os.path.exists(Cover_Path):
                os.makedirs(Cover_Path)
            
            for bv, url in videos.items():
                current_count += 1
                message = f"[{current_count}/{MaxCount}]:视频封面 {bv} ({fav_name})"
                logging.info(message)
                
                if url and isinstance(url, str) and url.startswith(('http://', 'https://')):
                    future = executor.submit(requests.get, url, headers=headers)
                    future_to_info[future] = {"bv": bv, "path": Cover_Path}
                else:
                    logging.warning(f'已跳过无效的URL (bv: {bv}): "{url}"')

        for future in futures.as_completed(future_to_info):
            info = future_to_info[future]
            bv = info['bv']
            path = info['path']
            try:
                response = future.result()
                if response.status_code == 200:
                    # Basic check to see if content is an image
                    if 'image' in response.headers.get('Content-Type', ''):
                        with open(os.path.join(path, f'{bv}.jpg'), 'wb') as f1:
                            f1.write(response.content)
                    else:
                        logging.warning(f'bv {bv} 的URL内容似乎不是图片, Content-Type: {response.headers.get("Content-Type")}')
                else:
                    logging.warning(f'bv {bv} 的封面爬取失败，状态码: {response.status_code}')
            except Exception as exc:
                logging.error(f'bv {bv} 的封面爬取失败，出现异常: {exc}')


def GetFace(PhotoURL_filename):
    with open(PhotoURL_filename, 'r', encoding='utf-8') as fp:
        PhotoURL_dict = json.load(fp)
    
    Face_Path = 'up头像/'
    if not os.path.exists(Face_Path):
        os.makedirs(Face_Path)

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Referer': 'https://www.bilibili.com/'
    }

    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_mid = {}
        count = 0
        MaxCount = len(PhotoURL_dict)
        
        for mid, url in PhotoURL_dict.items():
            count += 1
            message = f"[{count}/{MaxCount}]:up头像{mid}"
            logging.info(message)
            
            if url and isinstance(url, str) and url.startswith(('http://', 'https://')):
                future = executor.submit(requests.get, url, headers=headers)
                future_to_mid[future] = mid
            else:
                logging.warning(f'已跳过无效的URL (mid: {mid}): "{url}"')

        for future in futures.as_completed(future_to_mid):
            mid = future_to_mid[future]
            try:
                response = future.result()
                if response.status_code == 200:
                    with open(os.path.join(Face_Path, f'{mid}.jpg'), 'wb') as f1:
                        f1.write(response.content)
                else:
                    logging.warning(f'mid为 {mid} 的头像爬取失败，状态码: {response.status_code}')
            except Exception as exc:
                logging.error(f'mid为 {mid} 的头像爬取失败，出现异常: {exc}')


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        filename='bilibili_crawler.log',
        filemode='w'
    )

    path1 = '收藏夹信息/'  # 存放信息的文件夹
    path2 = '视频封面/'  # 放视频封面的文件夹
    path3 = 'up头像/'  # 放up主头像的文件夹

    if not os.path.exists(path1):
        os.makedirs(path1)
    if not os.path.exists(path2):
        os.makedirs(path2)
    if not os.path.exists(path3):
        os.makedirs(path3)

    time_list = []
    STime = time.perf_counter()
    GetFavoriteID(path1, 2015058255)  # 自己账号的uid
    GetALLFavorite(path1)
    SetPhotoURL(path1)
    GetCover('视频封面url.json')
    GetFace('up头像url.json')
    ETime = time.perf_counter()
    time_list.append(time.strftime("%M:%S", time.gmtime(ETime - STime)))

    STime = time.perf_counter()
    view(path1, './收藏夹信息.xlsx')
    ETime = time.perf_counter()
    time_list.append(time.strftime("%M:%S", time.gmtime(ETime - STime)))
    logging.info(f"执行爬取代码所用时间：{time_list[0]}")
    logging.info(f"将数据写入excel文件所用时间: {time_list[1]}")