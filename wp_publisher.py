"""
WordPress REST API 통신: 포스트 생성/업데이트 + Polylang 통합
"""

import requests
import json
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin


class WordPressPublisher:
    def __init__(self, wordpress_url, username, password):
        """
        WordPress 퍼블리셔 초기화

        Args:
            wordpress_url: WordPress 사이트 URL (예: http://localhost)
            username: WordPress 사용자명
            password: WordPress 앱 비밀번호
        """
        self.wordpress_url = wordpress_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)
        self.rest_url = urljoin(self.wordpress_url, '/wp-json/wp/v2/')

    def test_connection(self):
        """
        WordPress 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            response = requests.get(
                urljoin(self.rest_url, 'posts?per_page=1'),
                auth=self.auth,
                timeout=5
            )
            if response.status_code == 200:
                print("✅ WordPress 연결 성공")
                return True
            else:
                print(f"❌ WordPress 연결 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            return False

    def publish_post(self, title, content, language, metadata=None, post_id=None):
        """
        WordPress에 포스트 게시 또는 업데이트

        Args:
            title: 포스트 제목
            content: 포스트 HTML 컨텐츠
            language: 언어 코드 ('ko' 또는 'en')
            metadata: 추가 메타데이터 (옵션)
            post_id: 기존 포스트 ID (None이면 새로 생성)

        Returns:
            dict: {
                'success': bool,
                'post_id': int,
                'url': str,
                'error': str (실패 시)
            }
        """
        # 언어 코드 매핑
        language_map = {
            'ko': 'ko_KR',
            'en': 'en_US'
        }
        polylang_language = language_map.get(language, language)

        # 포스트 데이터
        post_data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'meta': {
                'language': language,
                'obsidian_language': language,
            }
        }

        # 추가 메타데이터
        if metadata:
            post_data['meta'].update(metadata)

        try:
            if post_id:
                # 기존 포스트 업데이트
                response = requests.post(
                    urljoin(self.rest_url, f'posts/{post_id}'),
                    auth=self.auth,
                    json=post_data,
                    timeout=10
                )
                action = "업데이트"
            else:
                # 새 포스트 생성
                response = requests.post(
                    urljoin(self.rest_url, 'posts'),
                    auth=self.auth,
                    json=post_data,
                    timeout=10
                )
                action = "생성"

            # 응답 처리
            if response.status_code in [200, 201]:
                result = response.json()
                post_id = result.get('id')
                post_url = result.get('link')

                print(f"✅ 포스트 {action} 성공: {title} (ID: {post_id})")

                # Polylang 언어 설정 (POST 요청 후)
                self._set_polylang_language(post_id, polylang_language)

                return {
                    'success': True,
                    'post_id': post_id,
                    'url': post_url,
                }

            else:
                error_msg = response.json().get('message', f"HTTP {response.status_code}")
                print(f"❌ 포스트 {action} 실패: {title} - {error_msg}")
                return {
                    'success': False,
                    'post_id': post_id,
                    'error': error_msg
                }

        except Exception as e:
            print(f"❌ API 오류: {e}")
            return {
                'success': False,
                'post_id': post_id,
                'error': str(e)
            }

    def _set_polylang_language(self, post_id, language):
        """
        Polylang 언어 설정

        Args:
            post_id: WordPress 포스트 ID
            language: 언어 코드 (예: 'ko_KR', 'en_US')
        """
        try:
            # Polylang REST API를 통해 언어를 설정합니다
            # term_id: ko_KR = 3, en_US = 6
            language_map = {
                'ko_KR': 3,
                'en_US': 6,
            }

            lang_id = language_map.get(language)
            if not lang_id:
                print(f"  ⚠️ 지원하지 않는 언어 코드: {language}")
                return

            data = {
                'meta': {
                    '_polylang_post_language': lang_id
                }
            }
            response = requests.post(
                urljoin(self.rest_url, f'posts/{post_id}'),
                auth=self.auth,
                json=data,
                timeout=10
            )
            if response.status_code in [200, 201]:
                print(f"  → Polylang 언어 설정: {language}")
            else:
                print(f"  ⚠️ Polylang 언어 설정 응답: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️ Polylang 언어 설정 실패: {e}")

    def get_post_by_title(self, title, language):
        """
        제목으로 포스트 검색

        Args:
            title: 포스트 제목
            language: 언어 코드

        Returns:
            dict: 포스트 데이터 또는 None
        """
        try:
            response = requests.get(
                urljoin(self.rest_url, f'posts?search={title}&per_page=1'),
                auth=self.auth,
                timeout=10
            )

            if response.status_code == 200:
                posts = response.json()
                if posts:
                    return posts[0]
            return None

        except Exception as e:
            print(f"❌ 포스트 검색 오류: {e}")
            return None

    def delete_post(self, post_id, force=True):
        """
        포스트 삭제

        Args:
            post_id: WordPress 포스트 ID
            force: 완전 삭제 여부 (True = 휴지통 거치지 않고 삭제)

        Returns:
            bool: 성공 여부
        """
        try:
            force_param = '?force=true' if force else ''
            response = requests.delete(
                urljoin(self.rest_url, f'posts/{post_id}{force_param}'),
                auth=self.auth,
                timeout=10
            )

            if response.status_code in [200, 204]:
                print(f"✅ 포스트 삭제 성공: ID {post_id}")
                return True
            else:
                print(f"❌ 포스트 삭제 실패: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 삭제 오류: {e}")
            return False
