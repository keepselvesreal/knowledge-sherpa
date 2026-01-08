<?php
/**
 * GeneratePress Child Theme Functions
 */

/**
 * 1. 테마 전환 시 부모 테마 설정을 자식 테마에 동기화
 *
 * 새로운 자식 테마가 활성화될 때 부모 테마의 사이드바 설정을
 * 자식 테마에 복사하여 설정이 초기화되는 것을 방지
 */
add_action('after_switch_theme', 'sync_parent_sidebar_to_child');
function sync_parent_sidebar_to_child() {
    $parent_mods = get_option('theme_mods_generatepress', array());
    $child_mods = get_option('theme_mods_generatepress-child', array());

    // 자식 테마의 설정이 비어있으면 부모 테마의 설정을 복사
    if (empty($child_mods) && !empty($parent_mods)) {
        update_option('theme_mods_generatepress-child', $parent_mods);
    }
}

/**
 * 2. sidebar-2에 categories-1 위젯 항상 유지
 *
 * 모든 페이지 로드 시 sidebar-2에 카테고리 위젯이 있는지 확인하고,
 * 없으면 자동으로 추가합니다.
 *
 * 주의: 이 함수는 데이터베이스에 위젯을 추가할 뿐,
 * 실제 화면 출력은 각 템플릿에서 generate_construct_sidebars()
 * 호출 시에만 일어납니다.
 *
 * 영향 범위:
 * - archive.php (범주별 페이지): generate_construct_sidebars() 호출 ✅
 * - single.php (개별 포스트): generate_construct_sidebars() 호출 ✅
 * - front-page.php (메인 페이지): 출력 코드 없음 (사이드바 안 보임)
 */
add_action('wp_loaded', 'ensure_sidebar_categories_widget');
function ensure_sidebar_categories_widget() {
    $current_theme = get_stylesheet();
    $option_name = "theme_mods_{$current_theme}";
    $theme_mods = get_option($option_name, array());

    // sidebars_widgets 구조 확인 및 초기화
    if (!isset($theme_mods['sidebars_widgets'])) {
        $theme_mods['sidebars_widgets'] = array(
            'time' => time(),
            'data' => array()
        );
    }

    if (!isset($theme_mods['sidebars_widgets']['data'])) {
        $theme_mods['sidebars_widgets']['data'] = array();
    }

    // sidebar-2 초기화
    if (!isset($theme_mods['sidebars_widgets']['data']['sidebar-2'])) {
        $theme_mods['sidebars_widgets']['data']['sidebar-2'] = array();
    }

    // categories-1(카테고리 위젯)이 sidebar-2에 없으면 추가
    if (!in_array('categories-1', $theme_mods['sidebars_widgets']['data']['sidebar-2'])) {
        $theme_mods['sidebars_widgets']['data']['sidebar-2'][] = 'categories-1';
        $theme_mods['sidebars_widgets']['time'] = time();
        update_option($option_name, $theme_mods);
    }
}

/**
 * 3. 범주 페이지(archive.php)에서 페이지네이션 설정
 *
 * 범주별 페이지에서 한 페이지에 9개의 포스트를 표시합니다.
 * 3열 그리드 레이아웃에 맞춰 3행(9개)씩 표시됩니다.
 *
 * 적용 대상:
 * - 범주별 페이지 (is_archive())
 * - 검색 결과 페이지
 * - 기타 아카이브 페이지
 */
add_action('pre_get_posts', 'set_archive_posts_per_page');
function set_archive_posts_per_page($query) {
    if (!is_admin() && $query->is_main_query() && is_archive()) {
        $query->set('posts_per_page', 9);
    }
    return $query;
}

/**
 * 4. Application Passwords 로컬 개발 환경 허용
 *
 * WordPress는 기본적으로 HTTPS에서만 Application Passwords 사용을 허용하지만,
 * 로컬 개발 환경(HTTP)에서도 사용할 수 있도록 필터를 추가합니다.
 *
 * 주의: 프로덕션 환경에서는 반드시 HTTPS를 사용해야 합니다!
 */
add_filter('wp_is_application_passwords_available', '__return_true');

/**
 * 5. REST API 인증 확인
 *
 * REST API 요청 시 인증 상태를 확인합니다.
 * WordPress 관리자는 기본적으로 REST API 권한을 가지고 있으므로
 * 별도의 권한 추가는 필요하지 않습니다.
 */
add_filter('rest_authentication_errors', function($result) {
    // 이미 인증 에러가 있으면 그대로 반환
    if (is_wp_error($result)) {
        return $result;
    }

    // 인증된 사용자면 true 반환
    if (is_user_logged_in()) {
        return true;
    }

    // 그 외의 경우 기본 동작
    return $result;
});

/**
 * 6. 페이지별 스크립트/스타일 로드 (향후 확장용)
 *
 * 현재는 비어있지만, 다음과 같은 경우 여기에 추가 가능:
 * - archive.php 페이지에서만 특정 CSS 로드
 * - single.php 페이지에서만 목차(TOC) 스크립트 로드
 * - 전체 사이트에서 공통 스크립트 로드
 */
add_action("wp_enqueue_scripts", function() {
    // 추가 스크립트/스타일은 여기에 작성
});