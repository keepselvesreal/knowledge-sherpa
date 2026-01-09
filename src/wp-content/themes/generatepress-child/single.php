<?php
/**
 * The Template for displaying all single posts.
 *
 * @package GeneratePress
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

get_header(); ?>

	<div <?php generate_do_attr( 'content' ); ?>>
		<main <?php generate_do_attr( 'main' ); ?>>
			<?php
			/**
			 * generate_before_main_content hook.
			 *
			 * @since 0.1
			 */
			do_action( 'generate_before_main_content' );

			if ( generate_has_default_loop() ) {
				while ( have_posts() ) :

					the_post();

					generate_do_template_part( 'single' );

				endwhile;
			}

			/**
			 * generate_after_main_content hook.
			 *
			 * @since 0.1
			 */
			do_action( 'generate_after_main_content' );
			?>
		</main>
	</div>

	<?php
	/**
	 * generate_after_primary_content_area hook.
	 *
	 * @since 2.0
	 */
	do_action( 'generate_after_primary_content_area' );
	?>

	<aside class="sidebar-popular-posts">
		<?php
		// 전체 인기글 (조회수 기반)
		echo '<h3>인기글</h3>';
		echo do_shortcode('[wpp limit="1" stats_tag="views" order_by="views"]');

		// 현재 카테고리의 인기글
		$categories = get_the_category();
		if (!empty($categories)) {
			$category_id = $categories[0]->term_id;
			$category_name = $categories[0]->name;
			echo '<h3>' . esc_html($category_name) . ' 인기글</h3>';
			echo do_shortcode('[wpp limit="1" cat="' . $category_id . '" stats_tag="views" order_by="views"]');
		}
		?>
	</aside>

	<?php
	generate_construct_sidebars();

	get_footer();
