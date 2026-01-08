<?php
/**
 * Plugin Name: Polylang REST Connector
 * Description: Adds REST API endpoints for Polylang translation management
 * Version: 1.0.0
 * Author: Polylang REST Connector
 * License: GPL-2.0-or-later
 *
 * This plugin provides REST API endpoints to manage Polylang translations
 * since Polylang's native REST support is limited.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Polylang이 로드되었는지 확인
 */
function pll_rest_connector_check_polylang() {
    if ( ! function_exists( 'pll_save_post_translations' ) ) {
        add_action( 'admin_notices', function() {
            echo '<div class="error"><p>Polylang REST Connector: Polylang 플러그인이 필요합니다.</p></div>';
        } );
        return false;
    }
    return true;
}

/**
 * REST API 라우트 등록
 */
add_action( 'rest_api_init', function() {
    // Polylang이 활성화되지 않았으면 라우트 등록 중단
    if ( ! function_exists( 'pll_save_post_translations' ) ) {
        return;
    }
    // 번역 관계 설정 엔드포인트
    register_rest_route( 'pll/v1', '/link-translations', array(
        'methods'             => 'POST',
        'callback'            => 'pll_rest_link_translations',
        'permission_callback' => '__return_true',
        'args'                => array(
            'posts'     => array(
                'type'        => 'object',
                'required'    => true,
                'description' => 'Posts to link. Format: { "ko_KR": post_id, "en_US": post_id, ... }',
            ),
            'language'  => array(
                'type'        => 'string',
                'required'    => false,
                'description' => 'Primary language code (optional)',
            ),
        ),
    ) );

    // 포스트 언어 설정 엔드포인트
    register_rest_route( 'pll/v1', '/set-language', array(
        'methods'             => 'POST',
        'callback'            => 'pll_rest_set_language',
        'permission_callback' => '__return_true',
        'args'                => array(
            'post_id'  => array(
                'type'        => 'integer',
                'required'    => true,
                'description' => 'Post ID',
            ),
            'language' => array(
                'type'        => 'string',
                'required'    => true,
                'description' => 'Language code (e.g., ko_KR, en_US)',
            ),
        ),
    ) );

    // 포스트 정보 조회 엔드포인트 (번역 정보 포함)
    register_rest_route( 'pll/v1', '/post/(?P<id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => 'pll_rest_get_post_info',
        'permission_callback' => '__return_true',
    ) );
} );

/**
 * 번역 관계 설정 핸들러
 *
 * @param WP_REST_Request $request
 * @return WP_REST_Response
 */
function pll_rest_link_translations( $request ) {
    // Polylang 함수 존재 확인
    if ( ! function_exists( 'pll_save_post_translations' ) || ! function_exists( 'pll_set_post_language' ) ) {
        return rest_ensure_response( array(
            'success' => false,
            'message' => 'Polylang is not available',
        ) );
    }

    $posts    = $request->get_param( 'posts' );
    $language = $request->get_param( 'language' );

    // 입력값 검증
    if ( ! is_array( $posts ) || empty( $posts ) ) {
        return rest_ensure_response( array(
            'success' => false,
            'message' => 'Invalid posts parameter',
        ) );
    }

    try {
        // 각 포스트의 언어 설정 (옵션)
        if ( $language ) {
            foreach ( $posts as $lang_code => $post_id ) {
                if ( is_numeric( $post_id ) && get_post( $post_id ) ) {
                    pll_set_post_language( $post_id, $lang_code );
                }
            }
        }

        // 번역 관계 설정
        $result = pll_save_post_translations( $posts );

        if ( $result === false ) {
            return rest_ensure_response( array(
                'success' => false,
                'message' => 'Failed to save post translations',
                'posts'   => $posts,
            ) );
        }

        return rest_ensure_response( array(
            'success' => true,
            'message' => 'Post translations linked successfully',
            'posts'   => $posts,
        ) );

    } catch ( Exception $e ) {
        return rest_ensure_response( array(
            'success' => false,
            'message' => 'Error linking translations: ' . $e->getMessage(),
        ) );
    }
}

/**
 * 포스트 언어 설정 핸들러
 *
 * @param WP_REST_Request $request
 * @return WP_REST_Response
 */
function pll_rest_set_language( $request ) {
    // Polylang 함수 존재 확인
    if ( ! function_exists( 'pll_set_post_language' ) ) {
        return rest_ensure_response( array(
            'success' => false,
            'message' => 'Polylang is not available',
        ) );
    }

    $post_id  = $request->get_param( 'post_id' );
    $language = $request->get_param( 'language' );

    // 포스트 존재 확인
    if ( ! get_post( $post_id ) ) {
        return new WP_REST_Response( array(
            'success' => false,
            'message' => 'Post not found',
        ), 404 );
    }

    try {
        pll_set_post_language( $post_id, $language );

        return rest_ensure_response( array(
            'success'  => true,
            'message'  => sprintf( 'Language set to %s for post %d', $language, $post_id ),
            'post_id'  => $post_id,
            'language' => $language,
        ) );

    } catch ( Exception $e ) {
        return rest_ensure_response( array(
            'success' => false,
            'message' => 'Error setting language: ' . $e->getMessage(),
        ) );
    }
}

/**
 * 포스트 정보 조회 (번역 정보 포함)
 *
 * @param WP_REST_Request $request
 * @return WP_REST_Response
 */
function pll_rest_get_post_info( $request ) {
    // Polylang 함수 존재 확인
    if ( ! function_exists( 'pll_get_post_language' ) || ! function_exists( 'pll_get_post_translations' ) ) {
        return rest_ensure_response( array(
            'success' => false,
            'message' => 'Polylang is not available',
        ) );
    }

    $post_id = $request->get_param( 'id' );

    $post = get_post( $post_id );
    if ( ! $post ) {
        return new WP_REST_Response( array(
            'success' => false,
            'message' => 'Post not found',
        ), 404 );
    }

    // 현재 포스트의 언어
    $current_language = pll_get_post_language( $post_id );

    // 번역된 포스트들 (모든 언어)
    $translations = pll_get_post_translations( $post_id );

    return rest_ensure_response( array(
        'success'       => true,
        'post_id'       => $post_id,
        'title'         => $post->post_title,
        'language'      => $current_language,
        'translations'  => $translations ? $translations : array(),
    ) );
}