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

/**
 * 7. Easy Table of Contents 버튼 텍스트 변경
 *
 * 현재 언어에 따라 버튼 텍스트를 명시적으로 설정
 */
add_action('wp_footer', function() {
    // 개별 포스트 페이지인지 확인
    if ( !is_singular( 'post' ) ) {
        return;
    }
    ?>
    <script>
    (function() {
        const button = document.querySelector('.ez-toc-open-icon');
        if (!button) return;

        // 현재 언어 감지 (예: 'ko-KR', 'en-US')
        const lang = document.documentElement.lang || 'ko';

        // 언어 코드의 앞 2글자만 추출 (예: 'ko-KR' → 'ko', 'en-US' → 'en')
        const langPrefix = lang.split('-')[0];

        // 언어 코드 앞부분에 따른 버튼 텍스트 (명시적 선언)
        const texts = {
            'ko': '목차',      // 한국어
            'en': 'TOC'        // 영어
        };

        // 선언된 언어만 처리 (langPrefix가 texts에 있으면 텍스트 변경)
        if (texts[langPrefix]) {
            button.innerHTML = texts[langPrefix];
        }
    })();
    </script>
    <?php
}, 20);

/**
 * 8. 포스트 네비게이션 텍스트 커스터마이징
 *
 * 이전 글 네비게이션의 화살표 기호를 "이전 글: " 텍스트로 변경
 */
add_filter('generate_post_navigation_args', function($args) {
    $args['previous_format'] = '<div class="nav-previous"><span class="prev">이전 글: %link</span></div>';
    $args['next_format'] = '<div class="nav-next"><span class="next">다음 글: %link</span></div>';
    return $args;
});

/**
 * 9. 개별 포스트 페이지 breadcrumb 네비게이션
 *
 * 포스트가 속한 카테고리 계층을 표시합니다.
 * 예: book > it 또는 book-en > it-en (언어에 따라)
 *
 * Polylang 카테고리 slug 규칙: 범주명-ko (한국어), 범주명-en (영어)
 */
function generate_post_breadcrumb() {
    if ( ! is_singular( 'post' ) ) {
        return;
    }

    $categories = get_the_category();
    if ( empty( $categories ) ) {
        return;
    }

    // 현재 언어 감지 (Polylang)
    $current_lang = function_exists( 'pll_current_language' ) ? pll_current_language() : 'ko';
    $lang_suffix = ( $current_lang === 'en' ) ? '-en' : '-ko';

    // 첫 번째 카테고리의 계층을 표시
    $category = $categories[0];
    $breadcrumb_items = array();

    // 부모 카테고리부터 현재 카테고리까지 계층 구성
    $ancestors = get_ancestors( $category->term_id, 'category' );
    $ancestors = array_reverse( $ancestors );

    foreach ( $ancestors as $ancestor_id ) {
        $ancestor = get_term( $ancestor_id, 'category' );
        if ( ! is_wp_error( $ancestor ) ) {
            $breadcrumb_items[] = array(
                'name' => $ancestor->name,
                'term_id' => $ancestor->term_id,
            );
        }
    }

    // 현재 카테고리 추가
    $breadcrumb_items[] = array(
        'name' => $category->name,
        'term_id' => $category->term_id,
    );

    if ( empty( $breadcrumb_items ) ) {
        return;
    }

    // breadcrumb HTML 생성
    echo '<nav class="post-breadcrumb" aria-label="breadcrumb">';
    echo '<div class="breadcrumb-path">';

    foreach ( $breadcrumb_items as $index => $item ) {
        // 카테고리 페이지 URL 생성 (term_id 직접 사용 - DB 쿼리 최소화)
        $category_url = get_category_link( $item['term_id'] );

        // 영어인 경우 URL 수정 (Polylang 규칙)
        if ( $current_lang === 'en' && ! str_contains( $category_url, '/en/' ) ) {
            $category_url = str_replace( home_url(), home_url() . '/en', $category_url );
        }

        echo '<a href="' . esc_url( $category_url ) . '" class="breadcrumb-item">' . esc_html( $item['name'] ) . '</a>';

        if ( $index < count( $breadcrumb_items ) - 1 ) {
            echo '<span class="breadcrumb-separator"> / </span>';
        }
    }

    echo '</div>';
    echo '</nav>';
}

add_action( 'generate_before_content', 'generate_post_breadcrumb' );

