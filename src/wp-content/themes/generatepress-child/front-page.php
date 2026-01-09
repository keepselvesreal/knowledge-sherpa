<?php
get_header();
?>
<main id="main" class="site-main">
    <div class="container hero-section">
        <div class="hero-content">
            <h1><?php bloginfo("name"); ?></h1>
            <p><?php bloginfo("description"); ?></p>
        </div>

        <!-- 언어 선택 섹션 -->
        <div class="language-selector">
            <span class="language-label">언어 선택:</span>
            <div class="language-buttons">
                <a href="#" class="lang-btn" data-lang="ko">
                    🇰🇷 한국어
                </a>
                <a href="#" class="lang-btn" data-lang="en">
                    🇺🇸 English
                </a>
            </div>
        </div>

        <!-- 카테고리 카드 -->
        <div class="source-cards">
            <a href="#" class="source-card" data-category="book">
                <div class="source-card-image" style="background-image: url('<?php echo get_stylesheet_directory_uri(); ?>/images/book-icon.jpg');"></div>
                <div class="source-card-content">
                    <h2>📚 BOOK</h2>
                    <p class="card-desc-ko">지식을 담은 책들의 모음</p>
                    <p class="card-desc-en" style="display:none;">Collection of knowledge books</p>
                </div>
            </a>
            <a href="#" class="source-card" data-category="web">
                <div class="source-card-image" style="background-image: url('<?php echo get_stylesheet_directory_uri(); ?>/images/web-icon.jpg');"></div>
                <div class="source-card-content">
                    <h2>🌐 WEB</h2>
                    <p class="card-desc-ko">웹 자료 및 블로그</p>
                    <p class="card-desc-en" style="display:none;">Web resources and blogs</p>
                </div>
            </a>
            <a href="#" class="source-card" data-category="youtube">
                <div class="source-card-image" style="background-image: url('<?php echo get_stylesheet_directory_uri(); ?>/images/youtube-icon.jpg');"></div>
                <div class="source-card-content">
                    <h2>🎥 YOUTUBE</h2>
                    <p class="card-desc-ko">영상 강의 및 튜토리얼</p>
                    <p class="card-desc-en" style="display:none;">Video lectures and tutorials</p>
                </div>
            </a>
        </div>
    </div>
</main>

<script>
window.addEventListener('load', function() {
    // 1. 저장된 언어 또는 브라우저 언어 감지
    let selectedLang = localStorage.getItem('selectedLanguage');

    if (!selectedLang) {
        // 브라우저 언어 감지
        const browserLang = navigator.language || navigator.userLanguage;
        selectedLang = browserLang.startsWith('ko') ? 'ko' : 'en';
    }

    // 2. 초기 UI 업데이트
    updateUI(selectedLang);

    function updateUI(lang) {
        // 버튼 상태 업데이트
        document.querySelectorAll('.lang-btn').forEach(btn => {
            if (btn.dataset.lang === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // 라벨 텍스트 변경
        const label = document.querySelector('.language-label');
        if (label) {
            label.textContent = lang === 'en' ? 'Select Language:' : '언어 선택:';
        }

        // 카드 설명 텍스트 변경
        document.querySelectorAll('.source-card').forEach(card => {
            const koDesc = card.querySelector('.card-desc-ko');
            const enDesc = card.querySelector('.card-desc-en');

            if (lang === 'en') {
                if (koDesc) koDesc.style.display = 'none';
                if (enDesc) enDesc.style.display = 'block';
            } else {
                if (koDesc) koDesc.style.display = 'block';
                if (enDesc) enDesc.style.display = 'none';
            }
        });
    }

    // 3. 언어 선택 버튼 클릭 이벤트
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.dataset.lang;

            // localStorage에 저장
            localStorage.setItem('selectedLanguage', lang);
            selectedLang = lang;

            // UI 업데이트
            updateUI(lang);
        });
    });

    // 4. 카테고리 카드 클릭 이벤트
    document.querySelectorAll('.source-card').forEach(card => {
        card.addEventListener('click', function(e) {
            e.preventDefault();
            const category = this.dataset.category;
            const baseUrl = window.location.origin;

            // 선택된 언어에 따라 URL 구성
            let url;
            if (selectedLang === 'en') {
                url = baseUrl + '/en/category/' + category + '/';
            } else {
                url = baseUrl + '/category/' + category + '/';
            }

            window.location.href = url;
        });
    });
});
</script>
<?php
get_footer();
