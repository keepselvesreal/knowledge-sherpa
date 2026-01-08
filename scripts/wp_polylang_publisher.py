"""
재설계된 Polylang 번역 통합 퍼블리셔
- 한국어와 영어를 독립적인 포스트가 아닌 '번역 관계'로 관리
- Polylang REST API 커스텀 엔드포인트 활용
"""

import requests
import json
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin
import os
from pathlib import Path


class PolylangPublisher:
    """Polylang 번역 관계를 고려한 WordPress 퍼블리셔"""

    def __init__(self, wordpress_url, username, password):
        """
        WordPress REST API 통신 초기화

        Args:
            wordpress_url: WordPress URL (예: http://localhost)
            username: REST API 사용자명
            password: REST API 앱 비밀번호
        """
        self.wordpress_url = wordpress_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)
        self.rest_url = urljoin(self.wordpress_url, '/wp-json/wp/v2/')
        self.pll_rest_url = urljoin(self.wordpress_url, '/wp-json/pll/v1/')

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

    def test_polylang_endpoint(self):
        """
        Polylang 커스텀 REST 엔드포인트 테스트

        Returns:
            bool: 엔드포인트 사용 가능 여부
        """
        try:
            response = requests.get(
                urljoin(self.pll_rest_url, 'post/1'),
                auth=self.auth,
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Polylang REST 엔드포인트 사용 가능")
                return True
            else:
                print(f"⚠️ Polylang REST 엔드포인트: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ Polylang 엔드포인트 오류: {e}")
            return False

    def publish_post(self, title, content, language, metadata=None, post_id=None, category_name=None):
        """
        WordPress 포스트 생성 또는 업데이트 (Polylang 언어 설정 + 카테고리 포함)

        Args:
            title: 포스트 제목
            content: 포스트 HTML 컨텐츠
            language: 언어 코드 ('ko' 또는 'en')
            metadata: 추가 메타데이터
            post_id: 기존 포스트 ID (업데이트 시)
            category_name: 카테고리명 (옵션)

        Returns:
            dict: {
                'success': bool,
                'post_id': int,
                'url': str,
                'error': str
            }
        """
        # 언어 매핑
        language_map = {'ko': 'ko_KR', 'en': 'en_US'}
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

        # 카테고리 설정
        if category_name:
            category_id = self.get_or_create_category(category_name)
            if category_id:
                post_data['categories'] = [category_id]

        if metadata:
            post_data['meta'].update(metadata)

        try:
            if post_id:
                # 포스트 업데이트
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

            if response.status_code in [200, 201]:
                result = response.json()
                post_id = result.get('id')
                post_url = result.get('link')

                print(f"✅ 포스트 {action} 성공: {title} (ID: {post_id})")

                # Polylang 언어 설정
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
                    'post_id': post_id if 'post_id' in locals() else None,
                    'error': error_msg
                }

        except Exception as e:
            print(f"❌ API 오류: {e}")
            return {
                'success': False,
                'post_id': post_id if 'post_id' in locals() else None,
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
            response = requests.post(
                urljoin(self.pll_rest_url, 'set-language'),
                auth=self.auth,
                json={
                    'post_id': post_id,
                    'language': language
                },
                timeout=10
            )
            if response.status_code in [200, 201]:
                print(f"  → Polylang 언어 설정: {language}")
            else:
                print(f"  ⚠️ Polylang 언어 설정 응답: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️ Polylang 언어 설정 오류: {e}")

    def link_translations(self, ko_post_id, en_post_id):
        """
        한국어와 영어 포스트를 번역 관계로 링크

        ⚠️ 중요: 이 함수는 Polylang 커스텀 REST 엔드포인트를 사용합니다.
        플러그인 설치 필요: polylang-rest-connector.php

        Args:
            ko_post_id: 한국어 포스트 ID
            en_post_id: 영어 포스트 ID

        Returns:
            dict: {
                'success': bool,
                'message': str
            }
        """
        try:
            response = requests.post(
                urljoin(self.pll_rest_url, 'link-translations'),
                auth=self.auth,
                json={
                    'posts': {
                        'ko': ko_post_id,
                        'en': en_post_id
                    }
                },
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    print(f"  🔗 번역 관계 설정: 한국어({ko_post_id}) ↔ 영어({en_post_id})")
                    return {
                        'success': True,
                        'message': data.get('message', 'Translation linked')
                    }
                else:
                    print(f"  ❌ 번역 관계 설정 실패: {data.get('message')}")
                    return {
                        'success': False,
                        'message': data.get('message', 'Unknown error')
                    }
            else:
                error_msg = response.json().get('message', f"HTTP {response.status_code}")
                print(f"  ❌ 번역 관계 설정 실패: {error_msg}")
                return {
                    'success': False,
                    'message': error_msg
                }

        except Exception as e:
            print(f"  ❌ 번역 관계 설정 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_post_by_title(self, title):
        """
        제목으로 포스트 검색

        Args:
            title: 포스트 제목

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
            force: 완전 삭제 여부

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

    def get_or_create_category(self, category_name):
        """
        카테고리명으로 카테고리 ID를 조회하거나 없으면 생성

        Args:
            category_name: 카테고리명

        Returns:
            int: 카테고리 ID (실패 시 None)
        """
        if not category_name or category_name.strip() == '':
            return None

        try:
            # 1. 기존 카테고리 검색
            response = requests.get(
                urljoin(self.rest_url, f'categories?search={category_name}&per_page=1'),
                auth=self.auth,
                timeout=10
            )

            if response.status_code == 200:
                try:
                    categories = response.json()
                    if categories:
                        cat_id = categories[0]['id']
                        print(f"  📂 카테고리 조회: {category_name} (ID: {cat_id})")
                        return cat_id
                except ValueError as json_err:
                    print(f"  ⚠️ 카테고리 조회 JSON 파싱 오류: {json_err}")
                    print(f"  응답 내용 (처음 500자): {response.text[:500]}")
                    return None

            # 2. 카테고리가 없으면 생성
            create_response = requests.post(
                urljoin(self.rest_url, 'categories'),
                auth=self.auth,
                json={
                    'name': category_name,
                    'slug': category_name.lower().replace(' ', '-')
                },
                timeout=10
            )

            if create_response.status_code in [200, 201]:
                try:
                    cat_data = create_response.json()
                    cat_id = cat_data['id']
                    print(f"  ✨ 카테고리 생성: {category_name} (ID: {cat_id})")
                    return cat_id
                except ValueError as json_err:
                    print(f"  ⚠️ 카테고리 생성 JSON 파싱 오류: {json_err}")
                    print(f"  응답 내용 (처음 500자): {create_response.text[:500]}")
                    return None
            else:
                try:
                    error_msg = create_response.json().get('message', f"HTTP {create_response.status_code}")
                except:
                    error_msg = f"HTTP {create_response.status_code}"
                print(f"  ⚠️ 카테고리 생성 실패: {category_name} - {error_msg}")
                return None

        except Exception as e:
            print(f"  ⚠️ 카테고리 조회/생성 오류: {e}")
            return None

    def set_featured_image(self, post_id, file_path):
        """
        포스트에 특성 이미지(썸네일) 설정

        Args:
            post_id: WordPress 포스트 ID
            file_path: 이미지 파일 경로

        Returns:
            dict: {
                'success': bool,
                'media_id': int or None,
                'message': str
            }
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'media_id': None,
                'message': f'이미지 파일 없음: {file_path}'
            }

        try:
            # 1. 미디어 라이브러리에 이미지 업로드
            with open(file_path, 'rb') as image_file:
                files = {
                    'file': image_file
                }
                headers = {
                    'Content-Disposition': f'attachment; filename="{os.path.basename(file_path)}"'
                }

                upload_response = requests.post(
                    urljoin(self.rest_url, 'media'),
                    auth=self.auth,
                    files=files,
                    headers=headers,
                    timeout=30
                )

            if upload_response.status_code not in [200, 201]:
                error_msg = upload_response.json().get('message', f"HTTP {upload_response.status_code}")
                return {
                    'success': False,
                    'media_id': None,
                    'message': f'이미지 업로드 실패: {error_msg}'
                }

            media_data = upload_response.json()
            media_id = media_data.get('id')

            # 2. 포스트에 featured image 설정
            update_response = requests.post(
                urljoin(self.rest_url, f'posts/{post_id}'),
                auth=self.auth,
                json={
                    'featured_media': media_id
                },
                timeout=10
            )

            if update_response.status_code in [200, 201]:
                print(f"  🖼️ 썸네일 설정 완료 (Media ID: {media_id})")
                return {
                    'success': True,
                    'media_id': media_id,
                    'message': '썸네일 설정 성공'
                }
            else:
                error_msg = update_response.json().get('message', f"HTTP {update_response.status_code}")
                return {
                    'success': False,
                    'media_id': media_id,
                    'message': f'썸네일 설정 실패: {error_msg}'
                }

        except Exception as e:
            return {
                'success': False,
                'media_id': None,
                'message': f'썸네일 설정 오류: {str(e)}'
            }
