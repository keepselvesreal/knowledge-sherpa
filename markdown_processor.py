"""
마크다운 파일 처리: YAML 파싱, 마크다운 → HTML 변환
"""

import os
import re
from pathlib import Path
import frontmatter
import markdown


def parse_markdown_file(file_path):
    """
    마크다운 파일 읽기 및 메타데이터 + 컨텐츠 분리

    Args:
        file_path: 마크다운 파일 경로

    Returns:
        dict: {
            'title': str,
            'publish': bool,
            'language': str,
            'wp-post-id': int or None,
            'mirror_post_id': int or None,
            'content': str (HTML)
        }
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        metadata = post.metadata
        markdown_content = post.content

        # 필수 필드 확인
        if 'publish' not in metadata:
            return None  # publish 필드 없으면 무시

        publish = metadata.get('publish')
        if not publish:
            return None  # publish가 False면 무시

        # 메타데이터 정리
        processed_metadata = {
            'title': metadata.get('title', Path(file_path).stem),
            'publish': publish,
            'language': metadata.get('language', 'ko'),
            'wp-post-id': metadata.get('wp-post-id'),
            'mirror_post_id': metadata.get('mirror_post_id'),
            'group-id': metadata.get('group-id'),
            'raw_metadata': metadata,
        }

        # 마크다운 → HTML 변환
        html_content = markdown_to_html(markdown_content)
        processed_metadata['content'] = html_content

        return processed_metadata

    except Exception as e:
        print(f"❌ 파일 처리 오류 ({file_path}): {e}")
        return None


def markdown_to_html(markdown_content):
    """
    마크다운을 HTML로 변환

    Args:
        markdown_content: 마크다운 텍스트

    Returns:
        str: HTML 컨텐츠
    """
    extensions = [
        'extra',
        'toc',
        'codehilite',
        'tables',
        'fenced_code',
    ]

    html = markdown.markdown(markdown_content, extensions=extensions)

    # Obsidian 위키 링크 변환 [[link]] → HTML 링크
    html = convert_wiki_links(html)

    return html


def convert_wiki_links(html_content):
    """
    Obsidian 위키 링크 형식 [[link]] 또는 [[link|display text]] 변환

    Args:
        html_content: HTML 컨텐츠

    Returns:
        str: 변환된 HTML
    """
    # [[link|display text]] 형식
    html_content = re.sub(
        r'\[\[([^\|]+)\|([^\]]+)\]\]',
        r'<a href="#\1">\2</a>',
        html_content
    )

    # [[link]] 형식 (표시 텍스트 = 링크명)
    html_content = re.sub(
        r'\[\[([^\]]+)\]\]',
        r'<a href="#\1">\1</a>',
        html_content
    )

    return html_content


def save_metadata_to_file(file_path, metadata_key, metadata_value):
    """
    마크다운 파일에 메타데이터 저장 (임시 파일 사용으로 원본 안전성 보장)

    작동 방식:
    1. 임시 파일에 먼저 쓰기
    2. 유효성 검사
    3. 검사 통과 시에만 원본으로 이동
    4. 실패 시 원본은 절대 건드리지 않음

    Args:
        file_path: 마크다운 파일 경로
        metadata_key: 메타데이터 키 (예: 'wp-post-id')
        metadata_value: 메타데이터 값

    Returns:
        bool: 성공 여부
    """
    import shutil
    import tempfile

    temp_file = None

    try:
        # 1. 원본 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # 2. 메타데이터 파싱
        post = frontmatter.loads(original_content)

        # 3. 메타데이터 업데이트
        post.metadata[metadata_key] = metadata_value

        # 4. 새 컨텐츠 생성
        new_content = frontmatter.dumps(post)

        # 5. 유효성 검사: 컨텐츠가 비어있지 않은지 확인
        if not new_content or len(new_content) < len(original_content) - 100:
            print(f"❌ 메타데이터 저장 실패: 컨텐츠 손상 위험")
            return False

        # 6. 임시 파일에 먼저 쓰기 (원본 보호)
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=os.path.dirname(file_path),
            delete=False,
            suffix='.md'
        ) as tmp:
            temp_file = tmp.name
            tmp.write(new_content)

        # 7. 임시 파일이 제대로 작성되었는지 확인
        with open(temp_file, 'r', encoding='utf-8') as f:
            written_content = f.read()

        if not written_content or len(written_content) < len(original_content) - 100:
            os.unlink(temp_file)
            print(f"❌ 메타데이터 저장 실패: 임시 파일 검증 실패")
            return False

        # 8. 임시 파일을 원본으로 이동 (원자적 작업)
        shutil.move(temp_file, file_path)

        print(f"✅ 메타데이터 저장: {os.path.basename(file_path)} ({metadata_key}: {metadata_value})")
        return True

    except Exception as e:
        # 실패 시 임시 파일 정리
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)

        print(f"❌ 메타데이터 저장 오류: {e}")
        return False


def get_markdown_files(folder_path, exclude_folders=None):
    """
    폴더에서 마크다운 파일 찾기

    Args:
        folder_path: 대상 폴더 경로
        exclude_folders: 제외할 폴더 리스트 (기본값: ['templates', 'drafts'])

    Returns:
        list: 마크다운 파일 경로 리스트 (언어별 서브폴더 포함)
    """
    if exclude_folders is None:
        exclude_folders = ['templates', 'drafts', '.obsidian']

    markdown_files = []

    for root, dirs, files in os.walk(folder_path):
        # 제외 폴더 필터링
        dirs[:] = [d for d in dirs if d not in exclude_folders]

        for file in files:
            if file.endswith('.md') and not file.startswith('.'):
                markdown_files.append(os.path.join(root, file))

    return sorted(markdown_files)
