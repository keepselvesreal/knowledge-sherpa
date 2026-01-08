"""
다국어 포스트 관리: 한영 미러 포스트 연결
"""

from markdown_processor import save_metadata_to_file
import os


class LanguageManager:
    def __init__(self):
        """
        언어 관리자 초기화
        """
        self.language_posts = {
            'ko': {},  # {file_path: post_id}
            'en': {}
        }

    def register_post(self, file_path, language, post_id):
        """
        게시된 포스트를 언어별로 등록

        Args:
            file_path: 마크다운 파일 경로
            language: 언어 코드 ('ko' 또는 'en')
            post_id: WordPress 포스트 ID
        """
        if language not in self.language_posts:
            self.language_posts[language] = {}

        self.language_posts[language][file_path] = post_id
        print(f"  📝 등록: {language} - {os.path.basename(file_path)} (ID: {post_id})")

    def link_mirror_posts(self, ko_file_path, en_file_path):
        """
        한국어와 영어 포스트를 미러링으로 연결

        ⚠️ 안전성:
        - 저장 실패 시 원본 파일은 손상되지 않음
        - 부분 실패 가능: 한국어 저장 성공 후 영어 저장 실패 시,
          한국어 파일에만 mirror_post_id 저장됨

        Args:
            ko_file_path: 한국어 마크다운 파일 경로
            en_file_path: 영어 마크다운 파일 경로

        Returns:
            bool: 성공 여부
        """
        ko_post_id = self.language_posts['ko'].get(ko_file_path)
        en_post_id = self.language_posts['en'].get(en_file_path)

        if not (ko_post_id and en_post_id):
            print(f"  ⚠️ 미러링 연결 불가: 한국어({ko_post_id}) 또는 영어({en_post_id}) 포스트 ID 없음")
            return False

        # 한국어 파일에 영어 포스트 ID 저장
        ko_success = save_metadata_to_file(ko_file_path, 'mirror_post_id', en_post_id)

        # 영어 파일에 한국어 포스트 ID 저장
        en_success = save_metadata_to_file(en_file_path, 'mirror_post_id', ko_post_id)

        if ko_success and en_success:
            print(f"  🔗 미러링 연결 완료: {os.path.basename(ko_file_path)} ↔ {os.path.basename(en_file_path)}")
            return True
        elif ko_success or en_success:
            print(f"  ⚠️ 부분 미러링 연결: 한쪽만 성공")
            print(f"     한국어 저장: {'✅' if ko_success else '❌'}")
            print(f"     영어 저장: {'✅' if en_success else '❌'}")
            return False
        else:
            print(f"  ❌ 미러링 연결 실패: 두 파일 모두 저장 실패")
            return False

    def find_mirror_file(self, file_path, target_language='en'):
        """
        현재 파일의 미러 파일 찾기

        Args:
            file_path: 현재 마크다운 파일 경로
            target_language: 목표 언어 ('en' 또는 'ko')

        Returns:
            str: 미러 파일 경로 또는 None
        """
        file_name = os.path.basename(file_path)
        file_dir = os.path.dirname(file_path)

        if target_language == 'en':
            # 영어 버전 찾기
            en_dir = os.path.join(file_dir, 'en')
            mirror_path = os.path.join(en_dir, file_name)
        else:
            # 한국어 버전 찾기
            if file_dir.endswith('/en'):
                ko_dir = os.path.dirname(file_dir)
                mirror_path = os.path.join(ko_dir, file_name)
            else:
                return None

        if os.path.exists(mirror_path):
            return mirror_path

        return None

    def get_language_from_path(self, file_path):
        """
        파일 경로에서 언어 판단

        Args:
            file_path: 마크다운 파일 경로

        Returns:
            str: 언어 코드 ('ko' 또는 'en')
        """
        if '/english/' in file_path:
            return 'en'
        return 'ko'

    def get_summary(self):
        """
        언어별 게시 현황 요약

        Returns:
            str: 요약 정보
        """
        ko_count = len(self.language_posts['ko'])
        en_count = len(self.language_posts['en'])

        return f"\n📊 게시 현황:\n  🇰🇷 한국어: {ko_count}개\n  🇺🇸 영어: {en_count}개"
