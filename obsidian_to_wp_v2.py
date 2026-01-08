#!/usr/bin/env python3
"""
📚 재설계된 Obsidian → WordPress 게시 스크립트 (Polylang 번역 통합)

올바른 동작 방식:
1. 한국어 파일 먼저 생성 (또는 업데이트)
2. 영어 파일 생성 (또는 업데이트)
3. 두 포스트를 Polylang 번역 관계로 링크

사용법:
    python obsidian_to_wp_v2.py /path/to/obsidian/folder/
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from markdown_processor import parse_markdown_file, get_markdown_files
from wp_polylang_publisher import PolylangPublisher
from language_manager import LanguageManager


def setup_logging(log_file):
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def load_config(config_file='config.env'):
    """설정 파일 로드"""
    if not os.path.exists(config_file):
        print(f"❌ config.env 파일을 찾을 수 없습니다: {config_file}")
        sys.exit(1)

    load_dotenv(config_file)

    config = {
        'WORDPRESS_URL': os.getenv('WORDPRESS_URL'),
        'WORDPRESS_USERNAME': os.getenv('WORDPRESS_USERNAME'),
        'WORDPRESS_PASSWORD': os.getenv('WORDPRESS_PASSWORD'),
        'LOG_FILE': os.getenv('LOG_FILE', 'logs/obsidian_to_wp.log'),
    }

    required_keys = ['WORDPRESS_URL', 'WORDPRESS_USERNAME', 'WORDPRESS_PASSWORD']
    for key in required_keys:
        if not config[key]:
            print(f"❌ 필수 설정 누락: {key}")
            sys.exit(1)

    return config


def collect_language_pairs(publish_folder):
    """
    한국어와 영어 파일 쌍 수집

    전략:
    1. 모든 publish: true인 파일 수집
    2. 한국어 파일 기준으로 mirror_post_id 또는 폴더 구조로 영어 파일 찾기

    Returns:
        list: [
            {
                'title': str,
                'ko_file': str,
                'en_file': str or None,
                'ko_existing_id': int or None,
                'en_existing_id': int or None,
            }
        ]
    """
    markdown_files = get_markdown_files(publish_folder)

    # 전체 파일 메타데이터 인덱싱 (post_id → 파일 매핑)
    all_files = {}  # {file_path: metadata}
    post_id_to_file = {}  # {post_id: file_path}

    for file_path in markdown_files:
        metadata = parse_markdown_file(file_path)
        if not metadata or not metadata.get('publish'):
            continue

        all_files[file_path] = metadata

        # post_id로도 인덱싱
        post_id = metadata.get('wp-post-id')
        if post_id:
            post_id_to_file[post_id] = file_path

    # 한국어 파일 기준으로 쌍 구성
    pairs = []
    processed_ko = set()

    for ko_file, ko_metadata in all_files.items():
        # 이미 처리된 파일 스킵
        if ko_file in processed_ko:
            continue

        # 한국어 파일인지 확인
        if '/english/' in ko_file or '/en/' in ko_file:
            continue

        ko_post_id = ko_metadata.get('wp-post-id')

        # 영어 파일 찾기
        en_file = None
        en_post_id = None

        # 전략 1: mirror_post_id 사용 (가장 정확함)
        mirror_post_id = ko_metadata.get('mirror_post_id')
        if mirror_post_id and mirror_post_id in post_id_to_file:
            en_file = post_id_to_file[mirror_post_id]
            if en_file in all_files:
                en_post_id = all_files[en_file].get('wp-post-id')

        # 전략 2: 폴더 구조 활용 (mirror_post_id가 없으면)
        if not en_file:
            # english/ 폴더에서 같은 이름의 파일 찾기
            ko_dir = os.path.dirname(ko_file)
            en_dir = os.path.join(ko_dir, 'english')

            ko_basename = os.path.basename(ko_file)

            if os.path.exists(en_dir):
                for en_candidate in os.listdir(en_dir):
                    en_candidate_path = os.path.join(en_dir, en_candidate)
                    if en_candidate_path in all_files:
                        # 같은 파일명이면 매칭
                        if ko_basename == en_candidate:
                            en_file = en_candidate_path
                            en_post_id = all_files[en_file].get('wp-post-id')
                            break

        pair = {
            'title': ko_metadata.get('title', Path(ko_file).stem),
            'ko_file': ko_file,
            'en_file': en_file,
            'ko_existing_id': ko_post_id,
            'en_existing_id': en_post_id,
        }

        pairs.append(pair)
        processed_ko.add(ko_file)
        if en_file:
            processed_ko.add(en_file)

    return pairs


def process_pairs(pairs, publisher, config, publish_folder):
    """
    한국어/영어 포스트 쌍 처리 및 번역 관계 설정

    Args:
        pairs: 언어 쌍 리스트
        publisher: PolylangPublisher 인스턴스
        config: 설정 정보
        publish_folder: 게시 폴더 경로
    """
    stats = {
        'total': len(pairs),
        'ko_created': 0,
        'ko_updated': 0,
        'en_created': 0,
        'en_updated': 0,
        'linked': 0,
        'failed': 0,
    }

    for pair in pairs:
        print(f"\n📝 처리: {pair['title']}")
        print(f"   한국어: {os.path.basename(pair['ko_file'])}")
        if pair['en_file']:
            print(f"   영어: {os.path.basename(pair['en_file'])}")

        # 1. 한국어 포스트 생성/업데이트
        ko_metadata = parse_markdown_file(pair['ko_file'])
        ko_result = publisher.publish_post(
            title=ko_metadata['title'],
            content=ko_metadata['content'],
            language='ko',
            metadata={'obsidian_file_path': pair['ko_file']},
            post_id=pair['ko_existing_id']
        )

        if not ko_result['success']:
            print(f"   ❌ 한국어 포스트 처리 실패")
            stats['failed'] += 1
            continue

        ko_post_id = ko_result['post_id']
        if pair['ko_existing_id']:
            stats['ko_updated'] += 1
        else:
            stats['ko_created'] += 1

        # 한국어 포스트 ID 저장
        from markdown_processor import save_metadata_to_file
        save_metadata_to_file(pair['ko_file'], 'wp-post-id', ko_post_id)
        print(f"   ✅ 한국어 포스트: ID {ko_post_id}")

        # 2. 영어 파일이 있으면 처리
        en_post_id = None
        if pair['en_file']:
            en_metadata = parse_markdown_file(pair['en_file'])
            en_result = publisher.publish_post(
                title=en_metadata['title'],
                content=en_metadata['content'],
                language='en',
                metadata={'obsidian_file_path': pair['en_file']},
                post_id=pair['en_existing_id']
            )

            if not en_result['success']:
                print(f"   ❌ 영어 포스트 처리 실패")
                # 영어 실패해도 한국어는 이미 게시됨
                stats['failed'] += 1
                continue

            en_post_id = en_result['post_id']
            if pair['en_existing_id']:
                stats['en_updated'] += 1
            else:
                stats['en_created'] += 1

            # 영어 포스트 ID 저장
            save_metadata_to_file(pair['en_file'], 'wp-post-id', en_post_id)
            print(f"   ✅ 영어 포스트: ID {en_post_id}")

            # 3. 번역 관계 설정
            link_result = publisher.link_translations(ko_post_id, en_post_id)
            if link_result['success']:
                stats['linked'] += 1
                print(f"   ✅ 번역 관계 설정 완료")
            else:
                print(f"   ⚠️ 번역 관계 설정 실패: {link_result['message']}")
                stats['failed'] += 1

    # 결과 출력
    print("\n" + "="*60)
    print("📊 게시 완료 요약:")
    print(f"  총 문서 쌍: {stats['total']}")
    print(f"  한국어 생성: {stats['ko_created']}")
    print(f"  한국어 업데이트: {stats['ko_updated']}")
    print(f"  영어 생성: {stats['en_created']}")
    print(f"  영어 업데이트: {stats['en_updated']}")
    print(f"  번역 관계 설정: {stats['linked']}")
    print(f"  실패: {stats['failed']}")
    print("="*60)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Obsidian 마크다운을 WordPress에 게시합니다 (Polylang 번역 통합).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python obsidian_to_wp_v2.py /home/user/문서/obsidian/resources/books/my-book/
  python obsidian_to_wp_v2.py ~/문서/obsidian/
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

    if not args.folder:
        parser.print_help()
        sys.exit(1)

    publish_folder_path = os.path.expanduser(args.folder)

    # 폴더 존재 확인
    if not os.path.isdir(publish_folder_path):
        print(f"❌ 폴더를 찾을 수 없습니다: {publish_folder_path}")
        sys.exit(1)

    print(f"\n📂 게시 폴더: {publish_folder_path}\n")

    # 설정 로드
    config = load_config(args.config)

    # 로깅 설정
    setup_logging(config['LOG_FILE'])

    # WordPress 퍼블리셔 초기화
    publisher = PolylangPublisher(
        config['WORDPRESS_URL'],
        config['WORDPRESS_USERNAME'],
        config['WORDPRESS_PASSWORD']
    )

    # 연결 테스트
    if not publisher.test_connection():
        print("❌ WordPress 연결 실패")
        sys.exit(1)

    # Polylang 엔드포인트 테스트
    if not publisher.test_polylang_endpoint():
        print("⚠️ Polylang 커스텀 엔드포인트 사용 불가")
        print("   설치 필요: polylang-rest-connector.php")

    # 언어 쌍 수집
    pairs = collect_language_pairs(publish_folder_path)

    if not pairs:
        print("⚠️ publish: true인 마크다운 파일이 없습니다.")
        return

    print(f"📄 발견된 문서 쌍: {len(pairs)}개\n")

    # 처리
    process_pairs(pairs, publisher, config, publish_folder_path)

    print("\n✅ 완료!\n")


if __name__ == '__main__':
    main()
