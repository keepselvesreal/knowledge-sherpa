<?php
/**
 * The template for displaying posts within the loop (Card format).
 *
 * Customized for card grid layout
 *
 * @package GeneratePress
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

// 썸네일 URL 가져오기
$thumbnail_url = get_the_post_thumbnail_url( get_the_ID(), 'medium' );
if ( ! $thumbnail_url ) {
	// 썸네일이 없으면 기본 이미지 사용
	$thumbnail_url = get_stylesheet_directory_uri() . '/images/placeholder.jpg';
}
?>

<article id="post-<?php the_ID(); ?>" class="post-card">
	<div class="post-card-inner">
		<!-- 썸네일 -->
		<div class="post-card-image">
			<a href="<?php the_permalink(); ?>" title="<?php the_title_attribute(); ?>">
				<img src="<?php echo esc_url( $thumbnail_url ); ?>" alt="<?php the_title_attribute(); ?>" />
			</a>
		</div>

		<!-- 제목 -->
		<div class="post-card-content">
			<h3 class="post-card-title">
				<a href="<?php the_permalink(); ?>" title="<?php the_title_attribute(); ?>">
					<?php the_title(); ?>
				</a>
			</h3>
		</div>
	</div>
</article>
