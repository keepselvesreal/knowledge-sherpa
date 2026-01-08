#!/usr/bin/env python3
"""
Obsidian → WordPress 자동 게시 스크립트

사용법:
    python obsidian_to_wp.py /path/to/obsidian/folder/
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from markdown_processor import parse_markdown_file, get_markdown_files
from wp_publisher import WordPressPublisher
from language_manager import LanguageManager


# 로깅 설정
def setup_logging(log_file):
    """
    로깅 설정

    Args:
        log_file: 로그 파일 경로
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def load_config(config_file='config.env'):
    """
    config.env 파일에서 설정 로드

    Args:
        config_file: 설정 파일 경로

    Returns:
        dict: 설정 정보
    """
    if not os.path.exists(config_file):
        print(f"❌ config.env 파일을 찾을 수 없습니다: {config_file}")
        sys.exit(1)

    load_dotenv(config_file)

    config = {
        'WORDPRESS_URL': os.getenv('WORDPRESS_URL'),
        'WORDPRESS_USERNAME': os.getenv('WORDPRESS_USERNAME'),
        'WORDPRESS_PASSWORD': os.getenv('WORDPRESS_PASSWORD'),
        'LOG_FILE': os.getenv('LOG_FILE', 'logs/obsidian_to_wp.log'),
        'POLYLANG_LANGUAGE_KO': os.getenv('POLYLANG_LANGUAGE_KO', 'ko_KR'),
        'POLYLANG_LANGUAGE_EN': os.getenv('POLYLANG_LANGUAGE_EN', 'en_US'),
    }

    # 필수 설정 확인
    required_keys = ['WORDPRESS_URL', 'WORDPRESS_USERNAME', 'WORDPRESS_PASSWORD']
    for key in required_keys:
        if not config[key]:
            print(f"❌ 필수 설정 누락: {key}")
            sys.exit(1)

    return config


def publish_folder(publish_folder, config):
    """
    지정된 폴더의 마크다운 파일을 WordPress에 게시

    Args:
        publish_folder: 게시할 Obsidian 폴더 경로
        config: 설정 정보 (dict)
    """
    # 폴더 존재 확인
    if not os.path.isdir(publish_folder):
        print(f"❌ 폴더를 찾을 수 없습니다: {publish_folder}")
        sys.exit(1)

    print(f"\n📂 게시 폴더: {publish_folder}")

    # WordPress 퍼블리셔 초기화
    publisher = WordPressPublisher(
        config['WORDPRESS_URL'],
        config['WORDPRESS_USERNAME'],
        config['WORDPRESS_PASSWORD']
    )

    # 연결 테스트
    if not publisher.test_connection():
        print("❌ WordPress 연결 실패. 설정을 확인하세요.")
        sys.exit(1)

    # 언어 관리자
    lang_manager = LanguageManager()

    # 마크다운 파일 수집
    markdown_files = get_markdown_files(publish_folder)

    if not markdown_files:
        print("⚠️ publish: true인 마크다운 파일이 없습니다.")
        return

    print(f"📄 발견된 마크다운 파일: {len(markdown_files)}개\n")

    # 파일별 처리
    for file_path in markdown_files:
        # 파일 파싱
        metadata = parse_markdown_file(file_path)

        if not metadata:
            continue  # publish: true가 아니거나 오류 발생

        title = metadata.get('title')
        content = metadata.get('content')
        language = metadata.get('language', 'ko')
        existing_post_id = metadata.get('wp-post-id')

        print(f"\n📝 처리: {title}")
        print(f"   언어: {language}")
        print(f"   파일: {os.path.basename(file_path)}")

        # ⚠️ 순서 중요: 메타데이터 저장 검증 → WordPress 게시 → 메타데이터 저장
        # (메타데이터 저장이 안 되면 WordPress 게시도 중단)

        # 1. 사전 검증: 파일이 실제로 읽을 수 있는지 확인
        try:
            test_content = metadata.get('raw_metadata', {})
            if not test_content and not content:
                print(f"   ❌ 오류: 파일 내용이 비어있습니다.")
                continue
        except Exception as e:
            print(f"   ❌ 오류: 파일 검증 실패 - {e}")
            continue

        # 2. WordPress에 게시
        result = publisher.publish_post(
            title=title,
            content=content,
            language=language,
            metadata={'obsidian_file_path': file_path},
            post_id=existing_post_id
        )

        # 3. 게시 실패 시 여기서 중단 (파일 수정 없음)
        if not result['success']:
            print(f"   ❌ 오류: {result.get('error')}")
            print(f"   ⚠️ WordPress 게시 실패로 인해 파일은 수정되지 않았습니다.")
            continue

        # 4. 게시 성공 후에만 메타데이터 저장
        post_id = result['post_id']

        from markdown_processor import save_metadata_to_file
        save_success = save_metadata_to_file(file_path, 'wp-post-id', post_id)

        # 5. 메타데이터 저장 실패 시
        if not save_success:
            print(f"   ⚠️ 경고: WordPress 포스트는 생성되었지만(ID: {post_id})")
            print(f"           메타데이터 저장 실패로 파일이 수정되지 않았습니다.")
            print(f"   → 원본 파일은 손상되지 않았습니다.")
            continue

        # 6. 성공: 언어 관리자에 등록
        lang_manager.register_post(file_path, language, post_id)
        print(f"   ✅ 완료: WordPress 게시 + 메타데이터 저장")

    # 미러 포스트 연결
    print(f"\n🔗 미러 포스트 연결 시작...")
    _link_mirror_posts(publish_folder, lang_manager)

    # 요약 출력
    print(lang_manager.get_summary())
    print("\n✅ 완료!\n")


def _link_mirror_posts(publish_folder, lang_manager):
    """
    한국어와 영어 포스트를 자동으로 미러링 연결

    Args:
        publish_folder: 게시 폴더 경로
        lang_manager: LanguageManager 인스턴스
    """
    # 한국어 파일 수집
    ko_files = {}
    for ko_file in lang_manager.language_posts['ko'].keys():
        file_name = os.path.basename(ko_file)
        ko_files[file_name] = ko_file

    # 영어 폴더에서 대응하는 파일 찾기 (english 폴더)
    en_folder = os.path.join(publish_folder, 'english')
    if not os.path.exists(en_folder):
        print("  ⚠️ english 폴더가 없어 미러링 연결을 건너뜁니다.")
        return

    for en_file in lang_manager.language_posts['en'].keys():
        file_name = os.path.basename(en_file)
        if file_name in ko_files:
            ko_file = ko_files[file_name]
            lang_manager.link_mirror_posts(ko_file, en_file)
        else:
            print(f"  ⚠️ 대응하는 한국어 파일 없음: {file_name}")


def main():
    """
    메인 함수
    """
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(
        description='Obsidian 마크다운을 WordPress에 게시합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python obsidian_to_wp.py /home/user/문서/obsidian/resources/books/my-book/
  python obsidian_to_wp.py ~/문서/obsidian/
        """
    )

    parser.add_argument(
        'folder',
        nargs='?',
        help='게시할 Obsidian 폴더 경로'
    )

    parser.add_argument(
        '--config',
        default='config.env',
        help='설정 파일 경로 (기본값: config.env)'
    )

    args = parser.parse_args()

    # 폴더 경로 필수 확인
    if not args.folder:
        parser.print_help()
        sys.exit(1)

    # 상대경로를 절대경로로 변환
    publish_folder_path = os.path.expanduser(args.folder)

    # 설정 로드
    config = load_config(args.config)

    # 로깅 설정
    setup_logging(config['LOG_FILE'])

    # 폴더 게시
    publish_folder(publish_folder_path, config)


if __name__ == '__main__':
    main()
