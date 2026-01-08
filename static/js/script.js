const btn = document.getElementById('toggle-btn');
const sidebar = document.getElementById('mySidebar');

btn.addEventListener('click', () => {
    sidebar.classList.toggle('active');
});

