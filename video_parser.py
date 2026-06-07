"""
视频链接解析工具
支持：B站、YouTube等主流视频平台
"""
import re
import requests
from urllib.parse import urlparse, parse_qs

def parse_bilibili_url(url):
    """
    解析B站视频链接，获取直接视频URL
    注意：这只是一个示例，实际使用可能需要更复杂的逻辑
    """
    print(f"\n=== 解析B站链接 ===")
    print(f"原始链接: {url}")

    # 提取BV号
    bv_pattern = r'BV\w+'
    bv_match = re.search(bv_pattern, url)

    if bv_match:
        bv_id = bv_match.group()
        print(f"视频ID: {bv_id}")

        # 方法1：使用第三方API（需要安装 you-get 或 youtube-dl）
        print("\n推荐使用以下方法获取B站视频直链：")
        print("1. 安装 you-get: pip install you-get")
        print(f"2. 运行命令: you-get -i '{url}'")
        print("3. 查看输出的视频URL")

        # 方法2：使用在线解析网站
        print("\n或者使用在线解析网站：")
        print("- https://bilibili.iiilab.com/")
        print("- https://www.xbeibeix.com/api/bilibili/")

        return None

    return None

def parse_youtube_url(url):
    """
    解析YouTube视频链接
    """
    print(f"\n=== 解析YouTube链接 ===")
    print(f"原始链接: {url}")

    # 提取视频ID
    if 'youtube.com/watch' in url:
        parsed = urlparse(url)
        video_id = parse_qs(parsed.query).get('v', [None])[0]
    elif 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[-1].split('?')[0]
    else:
        video_id = None

    if video_id:
        print(f"视频ID: {video_id}")

        print("\n推荐使用以下方法获取YouTube视频直链：")
        print("1. 安装 yt-dlp: pip install yt-dlp")
        print(f"2. 运行命令: yt-dlp -f best --get-url '{url}'")

        print("\n或者使用在线解析网站：")
        print("- https://www.y2mate.com/")
        print("- https://savefrom.net/")

        return None

    return None

def get_video_info(url):
    """
    获取视频信息（通用方法）
    """
    print(f"\n=== 检测视频链接 ===")
    print(f"URL: {url}")

    # 判断视频平台
    if 'bilibili.com' in url or 'b23.tv' in url:
        return parse_bilibili_url(url)
    elif 'youtube.com' in url or 'youtu.be' in url:
        return parse_youtube_url(url)
    else:
        # 检查是否已经是直链
        if url.endswith(('.mp4', '.webm', '.avi', '.mov', '.mkv')):
            print("✅ 这已经是直接视频链接！可以直接使用。")
            return url
        else:
            print("❌ 无法识别的视频链接格式")
            return None

def test_video_url(url):
    """
    测试视频URL是否可访问
    """
    print(f"\n=== 测试视频URL ===")
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length', '0')

            print(f"✅ 视频URL可访问")
            print(f"内容类型: {content_type}")
            print(f"文件大小: {int(content_length) / 1024 / 1024:.2f} MB")
            return True
        else:
            print(f"❌ 无法访问，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("视频链接解析工具")
    print("=" * 60)

    print("\n使用方法：")
    print("1. 输入视频网页链接（B站、YouTube等）")
    print("2. 工具会告诉你如何获取直接视频URL")
    print("3. 使用获取到的URL调用豆包API")

    while True:
        print("\n" + "-" * 60)
        url = input("\n请输入视频链接（输入 'q' 退出）: ").strip()

        if url.lower() == 'q':
            print("退出程序")
            break

        if not url:
            print("请输入有效的URL")
            continue

        # 获取视频信息
        direct_url = get_video_info(url)

        # 如果已经是直链，测试可访问性
        if direct_url and direct_url.endswith(('.mp4', '.webm', '.avi', '.mov', '.mkv')):
            test_video_url(direct_url)

if __name__ == "__main__":
    main()
