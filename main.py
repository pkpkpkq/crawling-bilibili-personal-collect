import logging
import sys

from app.services.auth_service import verify_cookie_headers
from app.services.config_service import (
    DEFAULT_SETTINGS as SERVICE_DEFAULT_SETTINGS,
    ConfigDecodeError,
    ConfigFileMissingError,
    ConfigValidationError,
    load_config as load_config_service,
)
from app.services.crawl_service import CrawlRunResult, CrawlService


DEFAULT_SETTINGS = dict(SERVICE_DEFAULT_SETTINGS)


def load_config():
    """加载配置文件，合并默认设置。"""
    try:
        uid, cookie, settings = load_config_service()
    except ConfigFileMissingError:
        logging.error("配置文件 config.json 不存在")
        logging.error("请先运行 getcookie.py 来生成有效的 config.json 文件。")
        sys.exit(1)
    except ConfigDecodeError as exc:
        logging.error(f"配置文件 JSON 解析错误: {exc}")
        sys.exit(1)
    except ConfigValidationError:
        logging.error("配置文件中缺少 'uid'")
        sys.exit(1)

    if not cookie:
        cookie = ""
        logging.warning("配置文件中缺少 'cookie'，将无法爬取关注列表和未公开内容。")
        logging.warning("请运行 getcookie.py 获取有效 Cookie。")

    return uid, cookie, settings


def verify_cookie(headers):
    """验证Cookie是否有效。"""
    result = verify_cookie_headers(headers, timeout=5, require_login=False)
    if not result.valid and result.error:
        logging.warning(f"Cookie验证失败: {result.error}")
    return result.valid


def configure_logging(log_path: str = "bilibili_crawler.log") -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:  # pylint: disable=broad-except
            pass

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def run_headless(service: CrawlService | None = None) -> CrawlRunResult:
    uid, cookie, settings = load_config()
    crawl_service = service or CrawlService()
    return crawl_service.run_headless_crawl(uid=uid, cookie=cookie, settings=settings)


def main() -> int:
    configure_logging()
    result = run_headless()
    if result.success:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
