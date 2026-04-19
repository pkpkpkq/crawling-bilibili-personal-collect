import os
from pathlib import Path

import pytest

from database import (
    add_video_to_collection,
    get_connection,
    get_db_path,
    init_db,
    mark_unfavorited,
    record_crawl,
    save_following_ups,
    upsert_collection,
    upsert_video,
)


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _build_video_payload(
    *,
    av_id,
    bv_id,
    title,
    up_mid,
    up_name,
    up_face,
    fav_time,
    upload_time,
    publish_time,
    duration="00:10:00",
    invalid=False,
):
    return {
        "id": av_id,
        "BV": bv_id,
        "是否失效": invalid,
        "up主": {"ID": up_mid, "昵称": up_name, "头像": up_face},
        "视频信息": {
            "标题": title,
            "封面": f"https://example.invalid/{bv_id}.jpg",
            "简介": f"fixture intro for {title}",
            "时长": duration,
        },
        "观众数据": {"播放量": 1000, "收藏量": 200, "弹幕数量": 30},
        "三个时间": {
            "上传时间": upload_time,
            "发布时间": publish_time,
            "收藏时间": fav_time,
        },
    }


def _seed_fixture_rows(db_path):
    with get_connection(str(db_path)) as conn:
        upsert_collection(conn, 101, "Tech Picks", media_count=2, api_mtime=1710000001)
        upsert_collection(conn, 202, "Music Box", media_count=2, api_mtime=1710000002)

        videos = [
            _build_video_payload(
                av_id=9001,
                bv_id="BVTEST001",
                title="Pytest Fixture Intro",
                up_mid=3001,
                up_name="UP Tech",
                up_face="https://example.invalid/up-tech.jpg",
                fav_time="2024-01-01 08:00:00",
                upload_time="2023-12-20 12:00:00",
                publish_time="2023-12-22 09:30:00",
            ),
            _build_video_payload(
                av_id=9002,
                bv_id="BVTEST002",
                title="Proxy Model Patterns",
                up_mid=3002,
                up_name="UP Music",
                up_face="https://example.invalid/up-music.jpg",
                fav_time="2024-02-01 09:00:00",
                upload_time="2024-01-15 12:00:00",
                publish_time="2024-01-16 10:00:00",
                duration="00:05:30",
            ),
            _build_video_payload(
                av_id=9003,
                bv_id="BVTEST003",
                title="已失效视频",
                up_mid=3002,
                up_name="UP Music",
                up_face="https://example.invalid/up-music.jpg",
                fav_time="2024-03-01 10:00:00",
                upload_time="2024-02-01 12:00:00",
                publish_time="2024-02-02 10:00:00",
                invalid=True,
                duration="00:02:10",
            ),
        ]

        for video in videos:
            upsert_video(conn, video)

        add_video_to_collection(conn, "BVTEST001", 101, "2024-01-01 08:00:00")
        add_video_to_collection(conn, "BVTEST002", 101, "2024-02-01 09:00:00")
        add_video_to_collection(conn, "BVTEST002", 202, "2024-02-10 09:00:00")
        add_video_to_collection(conn, "BVTEST003", 202, "2024-03-01 10:00:00")
        mark_unfavorited(conn, "BVTEST003", 202)

        save_following_ups(
            conn,
            [
                {
                    "ID": 3001,
                    "昵称": "UP Tech",
                    "头像": "https://example.invalid/up-tech.jpg",
                },
                {
                    "ID": 3002,
                    "昵称": "UP Music",
                    "头像": "https://example.invalid/up-music.jpg",
                },
            ],
        )

        record_crawl(
            conn,
            duration_seconds=15.5,
            total_videos=3,
            new_videos=3,
            invalid_videos=1,
            unfav_videos=1,
            status="success",
        )
        record_crawl(
            conn,
            duration_seconds=4.2,
            total_videos=0,
            new_videos=0,
            invalid_videos=0,
            unfav_videos=0,
            status="failed",
        )


@pytest.fixture()
def seeded_fixture_db(tmp_path):
    db_path = Path(get_db_path(str(tmp_path)))
    init_db(str(db_path))
    _seed_fixture_rows(db_path)
    return db_path


@pytest.fixture()
def seeded_fixture_summary(seeded_fixture_db):
    summary = {"db_path": str(seeded_fixture_db)}
    with get_connection(str(seeded_fixture_db)) as conn:
        for table in (
            "collections",
            "videos",
            "video_collection",
            "following_ups",
            "crawl_history",
        ):
            summary[table] = conn.execute(
                f"SELECT COUNT(*) AS c FROM {table}"
            ).fetchone()["c"]
    return summary
