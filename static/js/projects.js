document.addEventListener('DOMContentLoaded', function () {
    const projectContainer = document.querySelector('[data-page="projects-list"]');
    if (!projectContainer) return;

    // ОБРАБОТКА КЛИКОВ (И ЛАЙКИ, И УЧАСТИЕ)
    projectContainer.addEventListener('click', function (e) {
        
        // 1. Клик по лайку
        const favBtn = e.target.closest('.project-fav-icon');
        if (favBtn) {
            e.preventDefault();
            const url = favBtn.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    if (data.favorited) {
                        favBtn.classList.remove('not-favorite');
                        favBtn.classList.add('favorite');
                    } else {
                        favBtn.classList.remove('favorite');
                        favBtn.classList.add('not-favorite');
                    }
                } else if (data.status === 'auth_required') {
                    alert('Пожалуйста, авторизуйтесь для добавления в избранное.');
                }
            })
            .catch(err => console.error(err));
            return;
        }

        // 2. Клик по кнопке участия
        const joinBtn = e.target.closest('.project-join-btn');
        if (joinBtn) {
            e.preventDefault();
            const url = joinBtn.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    if (data.joined) {
                        joinBtn.textContent = 'Вы участвуете';
                        joinBtn.classList.add('joined'); // можно стилизовать в CSS
                    } else {
                        joinBtn.textContent = 'Стать участником';
                        joinBtn.classList.remove('joined');
                    }
                } else {
                    alert('Действие недоступно');
                }
            })
            .catch(err => console.error(err));
        }
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});