<?php
get_header();
?>
<main id="main" class="site-main">
    <div class="container hero-section">
        <div class="hero-content">
            <h1><?php bloginfo("name"); ?></h1>
            <p><?php bloginfo("description"); ?></p>
        </div>
        <div class="source-cards">
            <a href="<?php echo home_url("/category/book/"); ?>" class="source-card">
                <div class="source-card-image" style="background-image: url('<?php echo get_stylesheet_directory_uri(); ?>/images/book-icon.jpg');"></div>
                <div class="source-card-content">
                    <h2>📚 BOOK</h2>
                    <p>지식을 담은 책들의 모음</p>
                </div>
            </a>
            <a href="<?php echo home_url("/category/web/"); ?>" class="source-card">
                <div class="source-card-image" style="background-image: url('<?php echo get_stylesheet_directory_uri(); ?>/images/web-icon.jpg');"></div>
                <div class="source-card-content">
                    <h2>🌐 WEB</h2>
                    <p>웹 자료 및 블로그</p>
                </div>
            </a>
            <a href="<?php echo home_url("/category/youtube/"); ?>" class="source-card">
                <div class="source-card-image" style="background-image: url('<?php echo get_stylesheet_directory_uri(); ?>/images/youtube-icon.jpg');"></div>
                <div class="source-card-content">
                    <h2>🎥 YOUTUBE</h2>
                    <p>영상 강의 및 튜토리얼</p>
                </div>
            </a>
        </div>
    </div>
</main>
<?php
get_footer();
